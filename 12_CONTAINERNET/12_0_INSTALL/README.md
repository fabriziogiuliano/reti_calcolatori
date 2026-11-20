# Containernet on Ubuntu 26.04

Installation guide for [Containernet](https://containernet.github.io/) on **Ubuntu 26.04 LTS**, using a patch that adds 26.04 support and a **conda** environment.

## Requirements

- Ubuntu 26.04 LTS (the Server edition is fine), with a user that can run `sudo`
- at least 2 CPUs, 4 GB of RAM and 30 GB of disk
- conda, installed as in [00_PYTHON_ENVIRONMENT_SETUP](../../00_PYTHON_ENVIRONMENT_SETUP) (check with `conda --version`)

## Installation

Containernet is installed in your home directory, outside the course repository.

### 1. Base packages

```bash
sudo apt-get update
sudo apt-get install -y git ansible
```

### 2. Download Containernet and apply the patch

Start from the directory of this README, inside your clone of `reti_calcolatori`:

```bash
PATCH="$PWD/containernet-ubuntu-26.04.patch"

cd ~
git clone https://github.com/containernet/containernet.git
cd containernet
git checkout 8e0aabef8f23def3961b30897dd486191d9bd693
git apply --check "$PATCH"
git apply "$PATCH"
cd ~
```

The patch only applies to the commit in the `git checkout` line. If `git apply --check` fails, make sure you ran the checkout and do not continue.

### 3. Install the dependencies with Ansible

```bash
cd ~
sudo ansible-playbook -i "localhost," -c local containernet/ansible/install.yml
```

This installs Docker CE, Open vSwitch, the Mininet dependencies and the OpenFlow controller. It takes several minutes.

If it stops and you need to run it again, first delete the directory created by the installer: `sudo rm -rf ~/openflow`.

### 4. Conda environment

```bash
conda create -n containernet python=3.14 -y
conda activate containernet

cd ~/containernet
pip install .
```

### 5. Check

```bash
cd ~/containernet
sudo "$CONDA_PREFIX/bin/python" examples/containernet_example.py
```

You should see `*** Results: 0% dropped (2/2 received)`. At the `containernet>` prompt, type `exit`.

Always run scripts with `sudo "$CONDA_PREFIX/bin/python"`, with the `containernet` environment active.
