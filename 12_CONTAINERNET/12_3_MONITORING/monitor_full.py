"""
monitor.py - the controller measures bandwidth and delay of the whole network.

Every SAMPLE seconds, for every switch:
  1. bandwidth: it asks the statistics of every port (PORT_STATS) and
     computes Mbit/s from the bytes counted since the previous sample;
  2. delay: it sends a probe packet out of every port, with the time it left.
     The switch at the other end of the link sends the probe back to the
     controller: delay = arrival time - departure time. The probe also tells
     which switch and port are on the other side, so the controller
     discovers the links by itself.

Forwarding is the simplest possible: every switch has two ports and sends
out of one port whatever enters from the other one.
"""
import struct
import time

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import (CONFIG_DISPATCHER, MAIN_DISPATCHER,
                                       set_ev_cls)
from os_ken.lib import hub
from os_ken.ofproto import ofproto_v1_3

SAMPLE = 1.0                  # seconds between two measurements
PROBE_ETHERTYPE = 0x88b5      # EtherType reserved for local experiments
PROBE_FORMAT = '!QId'         # switch id, port, departure time


class Monitor(app_manager.OSKenApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Monitor, self).__init__(*args, **kwargs)
        self.switches = {}    # dpid -> datapath
        self.ports = {}       # (dpid, port) -> (bytes tx, bytes rx, time)
        self.rate = {}        # (dpid, port) -> (Mbit/s tx, Mbit/s rx)
        self.links = {}       # (dpid, port) -> (other dpid, other port)
        self.delay = {}       # (dpid, port) -> ms towards the other end
        hub.spawn(self._sampler)

    # ------------------------------------------------------ switch setup

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features(self, ev):
        dp = ev.msg.datapath
        parser, ofp = dp.ofproto_parser, dp.ofproto
        self.switches[dp.id] = dp
        # forwarding: what enters from port 1 goes out of port 2, and back
        self._add_flow(dp, 10, parser.OFPMatch(in_port=1),
                       [parser.OFPActionOutput(2)])
        self._add_flow(dp, 10, parser.OFPMatch(in_port=2),
                       [parser.OFPActionOutput(1)])
        # probes from another switch come back to the controller
        self._add_flow(dp, 100, parser.OFPMatch(eth_type=PROBE_ETHERTYPE),
                       [parser.OFPActionOutput(ofp.OFPP_CONTROLLER,
                                               ofp.OFPCML_NO_BUFFER)])
        self.logger.info('switch s%d connected', dp.id)

    def _add_flow(self, dp, priority, match, actions):
        parser, ofp = dp.ofproto_parser, dp.ofproto
        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
        dp.send_msg(parser.OFPFlowMod(datapath=dp, priority=priority,
                                      match=match, instructions=inst))

    # ------------------------------------------------------ every second

    def _sampler(self):
        while True:
            hub.sleep(SAMPLE)
            for dp in list(self.switches.values()):
                parser, ofp = dp.ofproto_parser, dp.ofproto
                # 1. bandwidth: ask the counters of all the ports
                dp.send_msg(parser.OFPPortStatsRequest(dp, 0, ofp.OFPP_ANY))
                # 2. delay: a probe out of every port we know
                for (dpid, port) in list(self.ports):
                    if dpid == dp.id:
                        self._send_probe(dp, port)
            self._print_table()

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats(self, ev):
        dpid = ev.msg.datapath.id
        for st in ev.msg.body:
            if st.port_no > 0xff00:          # skip the internal LOCAL port
                continue
            key = (dpid, st.port_no)
            now = st.duration_sec + st.duration_nsec / 1e9   # switch clock
            if key in self.ports:
                tx0, rx0, t0 = self.ports[key]
                dt = now - t0
                if dt > 0:
                    self.rate[key] = ((st.tx_bytes - tx0) * 8 / dt / 1e6,
                                      (st.rx_bytes - rx0) * 8 / dt / 1e6)
            self.ports[key] = (st.tx_bytes, st.rx_bytes, now)

    def _send_probe(self, dp, port):
        parser, ofp = dp.ofproto_parser, dp.ofproto
        payload = struct.pack(PROBE_FORMAT, dp.id, port, time.time())
        frame = (b'\xff' * 6 + b'\x02\x00\x00\x00\x00\x01' +
                 struct.pack('!H', PROBE_ETHERTYPE) + payload)
        dp.send_msg(parser.OFPPacketOut(
            datapath=dp, buffer_id=ofp.OFP_NO_BUFFER,
            in_port=ofp.OFPP_CONTROLLER,
            actions=[parser.OFPActionOutput(port)], data=frame))

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in(self, ev):
        msg = ev.msg
        data = msg.data
        if len(data) < 14 or struct.unpack('!H', data[12:14])[0] != PROBE_ETHERTYPE:
            return
        src_dpid, src_port, sent = struct.unpack_from(PROBE_FORMAT, data, 14)
        self.links[(src_dpid, src_port)] = (msg.datapath.id,
                                            msg.match['in_port'])
        self.delay[(src_dpid, src_port)] = (time.time() - sent) * 1000

    # ------------------------------------------------------ output

    def _print_table(self):
        if not self.ports:
            return
        lines = ['',
                 'switch port   tx Mbit/s   rx Mbit/s   link       delay ms',
                 '------ ----   ---------   ---------   ---------  --------']
        for key in sorted(self.ports):
            dpid, port = key
            tx, rx = self.rate.get(key, (0.0, 0.0))
            if key in self.links:
                other = self.links[key]
                link = '-> s%d:%d' % other
                delay = '%8.1f' % self.delay[key]
            else:
                link, delay = '(host)', '       -'
            lines.append('s%-5d %4d   %9.2f   %9.2f   %-9s  %s'
                         % (dpid, port, tx, rx, link, delay))
        print('\n'.join(lines), flush=True)
