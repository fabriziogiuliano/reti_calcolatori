"""
rest_router.py - IPv4 router for OpenFlow 1.3 switches, configured via REST.

An os-ken application that replaces the old Ryu app `ryu.app.rest_router`
(os-ken no longer ships it). Every switch becomes a router: it answers ARP
for its own addresses, routes IPv4 packets between its subnets and towards
its gateways, and answers ping to its own addresses.

REST API (same URLs and JSON as Ryu's rest_router), on port 8080:

  POST /router/<dpid>   {"address": "10.1.1.254/24"}             add an address
  POST /router/<dpid>   {"gateway": "200.0.0.253"}               default route
  POST /router/<dpid>   {"destination": "172.16.0.0/16",
                         "gateway": "200.0.0.253"}               static route
  GET  /router/<dpid>   show the configuration (<dpid> can be "all")

<dpid> is the switch id with 16 hex digits, e.g. 0000000000000001 for s1.

Start it with run_controller.py (see README.md).
"""
import ipaddress
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import (CONFIG_DISPATCHER, MAIN_DISPATCHER,
                                       set_ev_cls)
from os_ken.lib import hub
from os_ken.lib.packet import arp, ethernet, icmp, ipv4, packet
from os_ken.ofproto import ether, ofproto_v1_3

REST_PORT = 8080
ROUTE_PRIORITY = 100       # priority of the flows installed by the router
ROUTE_COOKIE = 0x1         # marks our flows, to delete them on changes
FLOW_IDLE_TIMEOUT = 60     # seconds: unused flows expire
MAX_PENDING = 32           # packets kept per next hop while waiting for ARP


class Router(object):
    "Configuration and state of the router of one switch"

    def __init__(self, dpid):
        self.dpid = dpid
        # one MAC address for the whole router, derived from the dpid
        self.mac = '02:00:%02x:%02x:%02x:%02x' % tuple(
            (dpid >> s) & 0xff for s in (24, 16, 8, 0))
        self.addresses = []      # ipaddress.IPv4Interface
        self.routes = []         # (ipaddress.IPv4Network, gateway IPv4Address)
        self.arp_table = {}      # IPv4Address -> (mac, port)
        self.pending = {}        # next hop IPv4Address -> [(in_port, data)]

    def own_ip(self, ip):
        return any(a.ip == ip for a in self.addresses)

    def connected(self, ip):
        "Address of the router in the subnet of ip, or None"
        best = None
        for a in self.addresses:
            if ip in a.network and (best is None or
                                    a.network.prefixlen > best.network.prefixlen):
                best = a
        return best

    def next_hop(self, dst):
        "IP to send a packet for dst to: dst itself, a gateway, or None"
        if self.connected(dst):
            return dst
        best = None
        for net, gw in self.routes:
            if dst in net and (best is None or net.prefixlen > best[0].prefixlen):
                best = (net, gw)
        return best[1] if best else None

    def to_dict(self):
        return {
            'switch_id': '%016x' % self.dpid,
            'mac': self.mac,
            'address': [{'address_id': i + 1, 'address': str(a)}
                        for i, a in enumerate(self.addresses)],
            'route': [{'route_id': i + 1, 'destination': str(n),
                       'gateway': str(g)}
                      for i, (n, g) in enumerate(self.routes)],
        }


class RestRouter(app_manager.OSKenApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(RestRouter, self).__init__(*args, **kwargs)
        self.lock = threading.Lock()
        self.routers = {}        # dpid -> Router (also before the switch connects)
        self.datapaths = {}      # dpid -> datapath of the connected switches
        hub.spawn(self._serve_rest)

    # ---------------------------------------------------------------- REST

    def _serve_rest(self):
        app = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                app.logger.info('REST %s', fmt % args)

            def _reply(self, code, body):
                data = (json.dumps(body, indent=2) + '\n').encode()
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _dpids(self):
                parts = self.path.strip('/').split('/')
                if len(parts) != 2 or parts[0] != 'router':
                    return None
                if parts[1] == 'all':
                    return 'all'
                try:
                    return int(parts[1], 16)
                except ValueError:
                    return None

            def do_GET(self):
                dpid = self._dpids()
                if dpid is None:
                    return self._reply(404, {'error': 'use /router/<dpid>'})
                with app.lock:
                    if dpid == 'all':
                        routers = [app.routers[d] for d in sorted(app.routers)]
                    else:
                        routers = [app._router(dpid)]
                    self._reply(200, [r.to_dict() for r in routers])

            def do_POST(self):
                dpid = self._dpids()
                if dpid is None or dpid == 'all':
                    return self._reply(404, {'error': 'use /router/<dpid>'})
                try:
                    length = int(self.headers.get('Content-Length', 0))
                    body = json.loads(self.rfile.read(length) or b'{}')
                    details = app._configure(dpid, body)
                    result = {'result': 'success', 'details': details}
                    code = 200
                except (ValueError, KeyError) as e:
                    result = {'result': 'failure', 'details': str(e)}
                    code = 400
                self._reply(code, [{'switch_id': '%016x' % dpid,
                                    'command_result': [result]}])

        server = ThreadingHTTPServer(('0.0.0.0', REST_PORT), Handler)
        self.logger.info('REST API on http://localhost:%d/router/<dpid>',
                         REST_PORT)
        server.serve_forever()

    def _router(self, dpid):
        if dpid not in self.routers:
            self.routers[dpid] = Router(dpid)
        return self.routers[dpid]

    def _configure(self, dpid, body):
        "Apply a POST body; returns the text for the reply"
        with self.lock:
            r = self._router(dpid)
            if 'address' in body:
                addr = ipaddress.IPv4Interface(body['address'])
                if addr.network.prefixlen == 32:
                    raise ValueError('address needs a prefix, e.g. 10.0.0.1/24')
                if addr in r.addresses:
                    # same request again (e.g. the network was restarted)
                    details = 'Address already set [address_id=%d]' % (
                        r.addresses.index(addr) + 1)
                else:
                    r.addresses.append(addr)
                    details = 'Add address [address_id=%d]' % len(r.addresses)
            elif 'gateway' in body:
                gw = ipaddress.IPv4Address(body['gateway'])
                net = ipaddress.IPv4Network(body.get('destination', '0.0.0.0/0'))
                r.routes = [(n, g) for n, g in r.routes if n != net]
                r.routes.append((net, gw))
                details = 'Add route [route_id=%d]' % len(r.routes)
            else:
                raise ValueError('body must contain "address" or "gateway"')
            dp = self.datapaths.get(dpid)
        self.logger.info('s%d: %s %s', dpid, details, body)
        if dp is not None:
            self._delete_route_flows(dp)   # recompute routes with the new config
        return details

    # ----------------------------------------------------------- OpenFlow

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features(self, ev):
        dp = ev.msg.datapath
        parser, ofp = dp.ofproto_parser, dp.ofproto
        with self.lock:
            self.datapaths[dp.id] = dp
            r = self._router(dp.id)
            # a (re)connected switch may belong to a new network:
            # forget the learned hosts, keep the configuration
            r.arp_table.clear()
            r.pending.clear()
        self._delete_route_flows(dp)
        # table-miss: every unknown packet goes to the controller, whole
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofp.OFPP_CONTROLLER,
                                          ofp.OFPCML_NO_BUFFER)]
        self._add_flow(dp, 0, match, actions)
        self.logger.info('switch %016x connected', dp.id)

    def _add_flow(self, dp, priority, match, actions, idle=0, cookie=0):
        parser, ofp = dp.ofproto_parser, dp.ofproto
        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
        dp.send_msg(parser.OFPFlowMod(datapath=dp, priority=priority,
                                      match=match, instructions=inst,
                                      idle_timeout=idle, cookie=cookie))

    def _delete_route_flows(self, dp):
        parser, ofp = dp.ofproto_parser, dp.ofproto
        dp.send_msg(parser.OFPFlowMod(datapath=dp, command=ofp.OFPFC_DELETE,
                                      table_id=ofp.OFPTT_ALL,
                                      out_port=ofp.OFPP_ANY,
                                      out_group=ofp.OFPG_ANY,
                                      cookie=ROUTE_COOKIE,
                                      cookie_mask=0xffffffffffffffff))

    def _packet_out(self, dp, in_port, actions, data):
        parser, ofp = dp.ofproto_parser, dp.ofproto
        dp.send_msg(parser.OFPPacketOut(datapath=dp,
                                        buffer_id=ofp.OFP_NO_BUFFER,
                                        in_port=in_port, actions=actions,
                                        data=data))

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in(self, ev):
        msg = ev.msg
        dp = msg.datapath
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth is None:
            return
        with self.lock:
            r = self._router(dp.id)
            if eth.ethertype == ether.ETH_TYPE_ARP:
                self._handle_arp(dp, r, in_port, pkt.get_protocol(arp.arp),
                                 msg.data)
            elif eth.ethertype == ether.ETH_TYPE_IP:
                self._handle_ipv4(dp, r, in_port, pkt, msg.data)
            # everything else (IPv6, LLDP, ...) is dropped

    # ---------------------------------------------------------------- ARP

    def _learn(self, dp, r, ip, mac, port):
        "Remember where ip is, if it is in one of our subnets"
        if not r.connected(ip):
            return
        r.arp_table[ip] = (mac, port)
        for in_port, data in r.pending.pop(ip, []):
            self._forward(dp, r, in_port, data, mac, port)

    def _handle_arp(self, dp, r, in_port, a, data):
        src = ipaddress.IPv4Address(a.src_ip)
        dst = ipaddress.IPv4Address(a.dst_ip)
        self._learn(dp, r, src, a.src_mac, in_port)
        if a.opcode == arp.ARP_REQUEST and r.own_ip(dst):
            # "who has <our address>?" -> "it is us"
            reply = packet.Packet()
            reply.add_protocol(ethernet.ethernet(dst=a.src_mac, src=r.mac,
                                                 ethertype=ether.ETH_TYPE_ARP))
            reply.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                       src_mac=r.mac, src_ip=a.dst_ip,
                                       dst_mac=a.src_mac, dst_ip=a.src_ip))
            reply.serialize()
            parser = dp.ofproto_parser
            self._packet_out(dp, dp.ofproto.OFPP_CONTROLLER,
                             [parser.OFPActionOutput(in_port)], reply.data)
        elif a.opcode == arp.ARP_REQUEST and not r.own_ip(dst):
            # ARP between two hosts of the same subnet: behave as a switch
            parser = dp.ofproto_parser
            self._packet_out(dp, in_port,
                             [parser.OFPActionOutput(dp.ofproto.OFPP_FLOOD)],
                             data)

    def _arp_request(self, dp, r, ip):
        "Ask on all ports who has ip"
        own = r.connected(ip)
        req = packet.Packet()
        req.add_protocol(ethernet.ethernet(dst='ff:ff:ff:ff:ff:ff', src=r.mac,
                                           ethertype=ether.ETH_TYPE_ARP))
        req.add_protocol(arp.arp(opcode=arp.ARP_REQUEST,
                                 src_mac=r.mac, src_ip=str(own.ip),
                                 dst_mac='00:00:00:00:00:00', dst_ip=str(ip)))
        req.serialize()
        parser, ofp = dp.ofproto_parser, dp.ofproto
        self._packet_out(dp, ofp.OFPP_CONTROLLER,
                         [parser.OFPActionOutput(ofp.OFPP_FLOOD)], req.data)

    # --------------------------------------------------------------- IPv4

    def _handle_ipv4(self, dp, r, in_port, pkt, data):
        eth = pkt.get_protocol(ethernet.ethernet)
        ip = pkt.get_protocol(ipv4.ipv4)
        src = ipaddress.IPv4Address(ip.src)
        dst = ipaddress.IPv4Address(ip.dst)
        self._learn(dp, r, src, eth.src, in_port)

        if r.own_ip(dst):
            self._answer_ping(dp, r, in_port, pkt)
            return

        nh = r.next_hop(dst)
        if nh is None or not r.connected(nh):
            self.logger.info('s%d: no route to %s, dropped', dp.id, dst)
            return
        if nh in r.arp_table:
            mac, port = r.arp_table[nh]
            self._install_route(dp, r, dst, mac, port)
            self._forward(dp, r, in_port, data, mac, port)
        else:
            queue = r.pending.setdefault(nh, [])
            if len(queue) < MAX_PENDING:
                queue.append((in_port, data))
            self._arp_request(dp, r, nh)

    def _route_actions(self, dp, r, mac, port):
        parser = dp.ofproto_parser
        return [parser.OFPActionSetField(eth_src=r.mac),
                parser.OFPActionSetField(eth_dst=mac),
                parser.OFPActionDecNwTtl(),
                parser.OFPActionOutput(port)]

    def _install_route(self, dp, r, dst, mac, port):
        parser = dp.ofproto_parser
        match = parser.OFPMatch(eth_type=ether.ETH_TYPE_IP, ipv4_dst=str(dst))
        self._add_flow(dp, ROUTE_PRIORITY, match,
                       self._route_actions(dp, r, mac, port),
                       idle=FLOW_IDLE_TIMEOUT, cookie=ROUTE_COOKIE)
        self.logger.info('s%d: route %s -> port %d (next hop %s)',
                         dp.id, dst, port, mac)

    def _forward(self, dp, r, in_port, data, mac, port):
        "Send one packet now, as the flow would do"
        self._packet_out(dp, in_port, self._route_actions(dp, r, mac, port),
                         data)

    def _answer_ping(self, dp, r, in_port, pkt):
        eth = pkt.get_protocol(ethernet.ethernet)
        ip = pkt.get_protocol(ipv4.ipv4)
        ic = pkt.get_protocol(icmp.icmp)
        if ic is None or ic.type != icmp.ICMP_ECHO_REQUEST:
            return
        reply = packet.Packet()
        reply.add_protocol(ethernet.ethernet(dst=eth.src, src=r.mac,
                                             ethertype=ether.ETH_TYPE_IP))
        reply.add_protocol(ipv4.ipv4(dst=ip.src, src=ip.dst,
                                     proto=ip.proto, ttl=64))
        reply.add_protocol(icmp.icmp(type_=icmp.ICMP_ECHO_REPLY, code=0,
                                     csum=0, data=ic.data))
        reply.serialize()
        parser = dp.ofproto_parser
        self._packet_out(dp, dp.ofproto.OFPP_CONTROLLER,
                         [parser.OFPActionOutput(in_port)], reply.data)
