"""
template_write.py - the controller writes a rule into a switch, every 10 seconds.

Every 10 seconds, in s1, it writes the rule "drop what comes from h1"
(port 1), or removes it. Try it with h1 ping h2.

    python run_controller.py template_write
"""
from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import CONFIG_DISPATCHER, set_ev_cls
from os_ken.lib import hub


# The class name is free: os-ken uses it as the name of the app.
# It must be different from the other apps started together with this one.
class TemplateWrite(app_manager.OSKenApp):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.switches = []
        self.blocked = False
        hub.spawn(self.every_10_seconds)    # start PIECE 2 in the background

    # PIECE 1. An event: a switch connects to the controller.
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_connected(self, ev):
        self.switches.append(ev.msg.datapath)

    # PIECE 2. A loop: every 10 seconds, block or unblock h1 on s1.
    def every_10_seconds(self):
        while True:
            hub.sleep(10)
            self.blocked = not self.blocked
            for sw in self.switches:
                if sw.id == 1:
                    self.write_rule(sw, self.blocked)

    # PIECE 3. Write into the switch: a FLOW_MOD message.
    def write_rule(self, sw, block):
        p, ofp = sw.ofproto_parser, sw.ofproto
        match = p.OFPMatch(in_port=1)            # what enters s1 from h1
        if block:
            # no actions = drop; priority 100 wins over the normal forwarding (0)
            sw.send_msg(p.OFPFlowMod(datapath=sw, priority=100, match=match,
                                     instructions=[]))
            print('s1: rule written, drop what comes from h1')
        else:
            sw.send_msg(p.OFPFlowMod(datapath=sw, priority=100, match=match,
                                     command=ofp.OFPFC_DELETE_STRICT,
                                     out_port=ofp.OFPP_ANY, out_group=ofp.OFPG_ANY))
            print('s1: rule removed, h1 passes again')
