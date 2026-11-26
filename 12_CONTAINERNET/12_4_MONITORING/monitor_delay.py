"""
monitor_delay.py - every second, the delay of every link.

The controller sends a probe out of a switch port, with the time written inside.
The switch on the other side of the link gives it back to the controller:
delay = time now - time written in the probe.
"""
import time

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from os_ken.lib import hub

PROBE = 0x88b5      # EtherType of the probes (reserved for experiments)


class MonitorDelay(app_manager.OSKenApp):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.switches = []
        hub.spawn(self.every_second)

    # a switch connects: "send me the probes you receive"
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_connected(self, ev):
        sw = ev.msg.datapath
        p, ofp = sw.ofproto_parser, sw.ofproto
        to_controller = p.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)
        sw.send_msg(p.OFPFlowMod(datapath=sw, priority=100,
                                 match=p.OFPMatch(eth_type=PROBE),
                                 instructions=[p.OFPInstructionActions(
                                     ofp.OFPIT_APPLY_ACTIONS, [to_controller])]))
        self.switches.append(sw)

    # every second: a probe out of port 1 and port 2 of every switch
    def every_second(self):
        while True:
            hub.sleep(1)
            for sw in self.switches:
                for port in (1, 2):
                    text = 's%d port %d at %f' % (sw.id, port, time.time())
                    frame = (bytes(6 * [0xff]) + bytes(6) +          # MAC addresses
                             PROBE.to_bytes(2, 'big') + text.encode())
                    p, ofp = sw.ofproto_parser, sw.ofproto
                    sw.send_msg(p.OFPPacketOut(datapath=sw, buffer_id=ofp.OFP_NO_BUFFER,
                                               in_port=ofp.OFPP_CONTROLLER, data=frame,
                                               actions=[p.OFPActionOutput(port)]))

    # a probe comes back from the other side of a link
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def probe_back(self, ev):
        sent_from, sent_at = ev.msg.data[14:].decode().split(' at ')
        delay_ms = (time.time() - float(sent_at)) * 1000
        print('%s -> s%d port %d: %.1f ms' % (sent_from, ev.msg.datapath.id,
                                              ev.msg.match['in_port'], delay_ms))
