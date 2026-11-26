# 8. Exercises

[← Troubleshooting](07-troubleshooting.md) · [Home](README.md)

## Observe

1. **The first packet.** Restart the network, open Wireshark on `lo` with the filter `openflow_v4`, and run `h1 ping -c1 h2`. Find the `PACKET_IN` of the ARP request, the `PACKET_OUT` of the ARP reply, and the `FLOW_MOD` of the route. Draw the sequence and compare it with [how the router works](03-how-the-router-works.md).
2. **The counters.** Run `h1 ping -c10 h2`, then `dump-flows` on `s1`. How many packets went through the route rule, and how many through the controller? Why?
3. **TTL.** `h1 ping -c1 h2` shows `ttl=62`. What would you see with a third router? Check with `h1 traceroute -n h2` (install `traceroute` if missing): does it work? Why (look at what the router does when TTL reaches 0)?
4. **Rule expiry.** After a ping, wait 60 s and `dump-flows` again. Ping again: what does terminal 1 print?

## Configure

5. **Break the default route.** With the network running, set a wrong gateway on `s1`:
   ```bash
   curl -X POST -d '{"gateway": "200.0.0.99"}' http://localhost:8080/router/0000000000000001
   ```
   What happens to `h1 ping h2`? What does terminal 1 print? Fix it.
6. **A static route.** Copy `router_topology.py` and, in the copy, replace the two default routes with static routes only for the subnet on the other side (`{"destination": "192.168.1.0/24", "gateway": "200.0.0.253"}` on `s1`, and the symmetric one on `s2`). Restart the controller (it keeps the old routes otherwise), run the copy: does the ping still work? Try to ping an address outside all the subnets.
7. **A third subnet.** Add a host `h3` on `s2` with address `172.16.0.3/24`, and give `s2` the address `172.16.0.254/24`. What do you need to change so that `h1` reaches `h3`?

## Extend the code

8. **DELETE.** Add `DELETE /router/<dpid>` with `{"route_id": 1}` to remove a route (look at `do_POST` and `_configure` in [`rest_router.py`](../rest_router.py); remember to delete the route rules from the switch).
9. **One rule per subnet.** For destinations reached through a gateway, install one rule for the whole subnet (`ipv4_dst=(network, mask)`) instead of one per host. Compare the number of rules with `dump-flows`.
10. **ICMP errors.** When there is no route, the router just drops the packet. Make it answer with an ICMP *Destination Unreachable* to the sender, as a real router does.
