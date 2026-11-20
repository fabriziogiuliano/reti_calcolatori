# Containernet on Ubuntu 26.04

Installation guide for [Containernet](https://containernet.github.io/) on **Ubuntu 26.04 LTS**, using a patch that adds 26.04 support and a **conda** environment.

## Requirements

- Ubuntu 26.04 LTS (the Server edition is fine), with a user that can run `sudo`
- at least 2 CPUs, 4 GB of RAM and 30 GB of disk
- [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install/linux-install): pick the installer for your architecture (`x86_64` or `aarch64`, check with `uname -m`)

> **License:** Anaconda's default channels are subject to the [Anaconda Terms of Service](https://www.anaconda.com/legal/terms/terms-of-service). If you cannot accept them, add `-c conda-forge --override-channels` to `conda create` in step 4.

## Installation

Run all commands from the same directory, for example your home directory.

### 1. Base packages

```bash
sudo apt-get update
sudo apt-get install -y git ansible
```

### 2. Download Containernet and apply the patch

```bash
git clone https://github.com/containernet/containernet.git
git clone https://github.com/fabriziogiuliano/reti_calcolatori.git

cd containernet
git checkout 8e0aabef8f23def3961b30897dd486191d9bd693
git apply --check ../reti_calcolatori/12_CONTAINERNET/12_0_INSTALL/containernet-ubuntu-26.04.patch
git apply ../reti_calcolatori/12_CONTAINERNET/12_0_INSTALL/containernet-ubuntu-26.04.patch
cd ..
```

The patch only applies to the commit in the `git checkout` line. If `git apply --check` fails, make sure you ran the checkout and do not continue.

### 3. Install the dependencies with Ansible

```bash
sudo ansible-playbook -i "localhost," -c local containernet/ansible/install.yml
```

This installs Docker CE, Open vSwitch, the Mininet dependencies and the OpenFlow controller. It takes several minutes.

If it stops and you need to run it again, first delete the directory created by the installer: `sudo rm -rf openflow`.

### 4. Conda environment

```bash
conda create -n containernet python=3.12 -y
conda activate containernet

cd containernet
pip install .
```

### 5. Check

```bash
sudo "$CONDA_PREFIX/bin/python" examples/containernet_example.py
```

You should see `*** Results: 0% dropped (2/2 received)`. At the `containernet>` prompt, type `exit`.

Always run scripts with `sudo "$CONDA_PREFIX/bin/python"`, with the `containernet` environment active.
