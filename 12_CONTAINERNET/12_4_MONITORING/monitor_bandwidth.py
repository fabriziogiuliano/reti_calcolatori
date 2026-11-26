"""
monitor_bandwidth.py - every second, the bandwidth of every port of every switch.
"""
from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from os_ken.lib import hub


class MonitorBandwidth(app_manager.OSKenApp):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.switches = []
        self.last_bytes = {}
        hub.spawn(self.every_second)

    # a switch connects
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_connected(self, ev):
        self.switches.append(ev.msg.datapath)

    # every second: "switch, send me the counters of your ports"
    def every_second(self):
        while True:
            hub.sleep(1)
            for sw in self.switches:
                sw.send_msg(sw.ofproto_parser.OFPPortStatsRequest(sw))

    # the answer: bytes sent now - bytes sent one second ago
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats(self, ev):
        for port in ev.msg.body:
            if port.port_no > 100:      # internal port of the switch
                continue
            key = (ev.msg.datapath.id, port.port_no)
            sent = port.tx_bytes - self.last_bytes.get(key, port.tx_bytes)
            self.last_bytes[key] = port.tx_bytes
            print('s%d port %d: %.2f Mbit/s' % (key[0], key[1], sent * 8 / 1e6))
