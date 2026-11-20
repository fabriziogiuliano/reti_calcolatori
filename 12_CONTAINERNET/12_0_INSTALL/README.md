# Containernet on Ubuntu 26.04

Installation guide for [Containernet](https://containernet.github.io/) on **Ubuntu 26.04 LTS**. Containernet officially supports only Ubuntu 22.04 and 24.04: the patch in this folder adds 26.04 support.

## Requirements

- Ubuntu 26.04 LTS (the Server edition is fine), with a user that can run `sudo`
- at least 2 CPUs, 4 GB of RAM and 30 GB of disk

## Installation

### 1. conda

conda must be installed as in [00_PYTHON_ENVIRONMENT_SETUP](../../00_PYTHON_ENVIRONMENT_SETUP), Step 1. Check:

```bash
conda --version
```

### 2. Create the conda environment `cn`

```bash
conda create -n cn python=3.14 -y
conda activate cn
```

Keep this terminal open: all the next steps run in it, with `cn` active.

### 3. Base packages

```bash
sudo apt-get update
sudo apt-get install -y git ansible
```

### 4. Download Containernet and apply the patch

```bash
cd ~
curl -fsSLO https://raw.githubusercontent.com/fabriziogiuliano/reti_calcolatori/main/12_CONTAINERNET/12_0_INSTALL/containernet-ubuntu-26.04.patch
git clone https://github.com/containernet/containernet.git
cd ~/containernet
git checkout 8e0aabef8f23def3961b30897dd486191d9bd693
git apply --check ~/containernet-ubuntu-26.04.patch
git apply ~/containernet-ubuntu-26.04.patch
```

`git apply --check` must print nothing. If it prints an error, do not continue.

### 5. Install the system dependencies with Ansible

```bash
cd ~
sudo ansible-playbook -i "localhost," -c local containernet/ansible/install.yml
```

This installs Docker CE, Open vSwitch, the Mininet dependencies and the OpenFlow controller. It takes several minutes.

If it stops and you need to run it again, first delete the directory created by the installer: `sudo rm -rf ~/openflow`.

### 6. Install Containernet in `cn`

```bash
cd ~/containernet
pip install .
```

### 7. Check

```bash
cd ~/containernet
sudo "$CONDA_PREFIX/bin/python" examples/containernet_example.py
```

You should see `*** Results: 0% dropped (2/2 received)`. At the `containernet>` prompt, type `exit`.

## Running scripts

In every new terminal:

```bash
conda activate cn
sudo "$CONDA_PREFIX/bin/python" your_script.py
```

`sudo` is needed to create the virtual hosts, switches and links; `$CONDA_PREFIX/bin/python` is the Python of `cn`, which `sudo` would not find by itself.
