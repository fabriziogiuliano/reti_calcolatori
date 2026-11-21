# 12 Network emulation with Containernet

[Containernet](https://containernet.github.io/) builds a whole network inside one machine: hosts, switches, routers and the links between them, with the bandwidth and the delay you choose. It is [Mininet](http://mininet.org/) plus Docker containers as hosts. The labs of this folder use it to study the **network layer**: OpenFlow switches, SDN controllers, monitoring and routing.

## Before you start

Install Containernet once, following [12_0_INSTALL](12_0_INSTALL/). It creates the conda environment **`cn`** (Python 3.14), separate from the environment `reti_calcolatori` of the other labs.

## Labs

| Folder | Topic | Kurose & Ross |
|---|---|---|
| [12_0_INSTALL](12_0_INSTALL/) | install Containernet on Ubuntu 26.04 (with a patch) and the environment `cn` | – |
| [12_1_SIMPLE_TOPOLOGY](12_1_SIMPLE_TOPOLOGY/) | two hosts and a switch; flow rules written by hand; enter a host with `mnexec` | 4.4 |
| [12_2_TEMPLATE_CONTROLLER](12_2_TEMPLATE_CONTROLLER/) | the pieces of an SDN controller (os-ken) in a minimal template | 5.5 |
| [12_3_MONITORING](12_3_MONITORING/) | the template becomes a tool: the controller measures bandwidth and delay of every link, every second | 5.5, 5.7 |
| [12_4_REST_ROUTER](12_4_REST_ROUTER/) | an SDN controller turns two switches into routers, configured via REST; [wiki](12_4_REST_ROUTER/docs/README.md) with diagrams | 4.4, 5.5 |
| [12_5_OSPF_FRR](12_5_OSPF_FRR/) | dynamic routing: four FRRouting routers in containers run OSPF (Dijkstra); link failures and costs | 5.2, 5.3 |

Follow them in order: each lab uses what the previous one introduced.

## Common rules

**Run the scripts with the Python of `cn`.** Mininet needs `sudo`, and `sudo` does not see the active conda environment:

```bash
conda activate cn
sudo "$CONDA_PREFIX/bin/python" script.py
```

**Controller and network are two programs.** In the labs with a controller (12_2, 12_3, 12_4) use two terminals: the controller first, without `sudo` (`python run_controller.py <app>`), then the network.

**Clean after an interrupted run.** If a script stops in the middle (Ctrl+C, closed terminal), the next run fails with `File exists` or `already in use`. Clean everything with:

```bash
sudo "$CONDA_PREFIX/bin/mn" -c
```

**Use tmux.** A dropped SSH connection kills the network; inside tmux it keeps running, and you get it back with `tmux attach`.
