# 7. Troubleshooting

[← Running the lab](06-running-the-lab.md) · [Home](README.md) · [Next: exercises →](08-exercises.md)

| Symptom | Cause | Fix |
|---|---|---|
| `curl: (7) Failed to connect to localhost port 8080` | the controller is not running | start it in terminal 1: `python run_controller.py rest_router` |
| `Unable to contact the remote controller at 127.0.0.1:6653` | same: Mininet cannot find the controller | start the controller **before** the network |
| `ModuleNotFoundError: No module named 'os_ken'` | os-ken not installed, or `cn` not active | `conda activate cn`, then `pip install os-ken==4.2.2` |
| `OSError: [Errno 98] Address already in use` when starting the controller | another controller is still running on 6653 or 8080 | stop it (Ctrl+C in its terminal), or find it with `ss -ltnp \| grep -E '6653\|8080'` |
| ping `100% packet loss` | the routers have no addresses or routes | check `curl http://localhost:8080/router/all`; look for `no route to ...` in terminal 1 |
| terminal 1 prints `no route to X, dropped` | no subnet and no route contain X | add the missing address or route with `POST` |
| `dump-flows` shows only `CONTROLLER:65535` | no traffic yet, or the rules expired after 60 s | ping, then dump again |
| `ovs-ofctl: ... version negotiation failed` | `ovs-ofctl` speaks OpenFlow 1.0 by default | add `-O OpenFlow13` |
| `File exists`, `already in use`, the network does not start | a previous run was interrupted | `sudo "$CONDA_PREFIX/bin/mn" -c`, then run again |
| the first ping is lost or slow | ARP and controller on the first packet | normal: from the second packet on the switch works alone |

## Look at what the controller sees

Terminal 1 prints every REST request, every switch connection and every installed route. When something does not work, read it first.

To see the OpenFlow messages on the wire, capture the controller channel:

```bash
sudo tcpdump -i lo -n tcp port 6653
```

or open Wireshark on `lo` with the filter `openflow_v4`: you see `PACKET_IN`, `FLOW_MOD` and `PACKET_OUT` with all their fields.
