"""
template_read.py - the pieces you need to write an os-ken controller tool.

It runs as it is: it prints when a switch connects, asks the port counters
every second and prints the answers. Copy it, rename it, fill the TODOs.

    python run_controller.py template_read
"""
from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from os_ken.lib import hub


# The class name is free: os-ken uses it as the name of the app.
# It must be different from the other apps started together with this one.
class TemplateRead(app_manager.OSKenApp):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.switches = []                 # your data: what you want to remember
        hub.spawn(self.every_second)       # start PIECE 2 in the background

    # PIECE 1. An event: a switch connects to the controller.
    # @set_ev_cls says WHICH message calls this function, and WHEN.
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_connected(self, ev):
        sw = ev.msg.datapath               # the switch: use it to send messages
        self.switches.append(sw)
        print('switch s%d connected' % sw.id)

    # PIECE 2. A loop: every second, ask something to every switch.
    def every_second(self):
        while True:
            hub.sleep(1)
            for sw in self.switches:
                # TODO: the request you need
                sw.send_msg(sw.ofproto_parser.OFPPortStatsRequest(sw))

    # PIECE 3. The answer to the request of PIECE 2.
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def answer(self, ev):
        sw = ev.msg.datapath
        for port in ev.msg.body:
            # TODO: compute what you need from the answer
            if port.port_no == sw.ofproto.OFPP_LOCAL:   # internal port of the switch
                continue
            
            print('s%d port %d: %d bytes sent' % (sw.id, port.port_no, port.tx_bytes))

