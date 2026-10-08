# 00 Python environment setup

Every lab of the course runs in the same conda environment, `reti_calcolatori`: Python 3.11 plus the few libraries the labs need (hypercorn for HTTP/2, aiosmtpd for the mail server). Set it up once, at the beginning of the course, and activate it every time you open a terminal.

## Files

| File | What it is |
|---|---|
| `setup_env.sh` | Creates the environment, installs the Python packages and checks the command-line tools |
| `requirements.txt` | The Python packages installed by `setup_env.sh` |

The course works on macOS, Linux and Windows. On Windows we use WSL, which is Linux running inside Windows: after Step 0, WSL users follow the Linux instructions everywhere.

---

## Step 0. Windows only: install WSL

The labs use Unix tools (`ncat`, `dig`, `tmux`), so on Windows we work inside WSL. Open PowerShell as administrator and run:
```
wsl --install
```
Restart the PC and open the *Ubuntu* app: from now on, every command of the course is typed there. More details: [install WSL](https://learn.microsoft.com/en-us/windows/wsl/install).

## Step 1. Install conda

Skip this step if `conda --version` already prints a version (a full Anaconda is fine too).

We use [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install), the minimal installer of conda: only conda and Python, everything else is installed when needed.

Download the installer and run it. `$(uname -m)` picks the right version for your processor by itself (`arm64` or `x86_64` on macOS, `x86_64` or `aarch64` on Linux).

**macOS**
```bash
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-$(uname -m).sh
bash Miniconda3-latest-MacOSX-$(uname -m).sh
```
**Linux and WSL**
```bash
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-$(uname -m).sh
bash Miniconda3-latest-Linux-$(uname -m).sh
```
On every system, answer `yes` to the license, press Enter to accept the default folder, and answer `yes` when it asks whether to initialize conda. Then close the terminal and open a new one, and check:
```bash
conda --version
```
**Expected output**
```
conda 24.11.1
```
Your version may be different.

## Step 2. Get the course folder

```bash
git clone https://github.com/fabriziogiuliano/reti_calcolatori.git
cd reti_calcolatori
```
If you already have the folder, update it with `git pull` instead.

## Step 3. Create the environment

Run this once:
```bash
bash 00_PYTHON_ENVIRONMENT_SETUP/setup_env.sh
```
It creates the environment `reti_calcolatori` (if it does not exist yet), installs the packages of `requirements.txt` and checks the command-line tools. The end of the output looks like this:
```
>>> Checking command-line tools
  [ok]      curl
  [ok]      nc
  [missing] telnet   (macOS: brew install ...  Linux: sudo apt install ...)
  [ok]      ncat
  ...
>>> Done. Run: conda activate reti_calcolatori
```
You can run it again at any time: it does not create the environment twice, it only updates the packages.

## Step 4. Activate the environment

```bash
conda activate reti_calcolatori
```
The prompt now starts with `(reti_calcolatori)`. Check the Python version:
```bash
python --version
```
**Expected output**
```
Python 3.11.17
```
Any `3.11.x` is fine.

Activate the environment in every new terminal and in every tmux pane: each one starts without it. To leave it, run `conda deactivate`.

## Step 5. Install the missing tools

If Step 3 printed some `[missing]` lines, install those tools.

**macOS**, with [Homebrew](https://brew.sh). `curl`, `nc`, `dig`, `host`, `tcpdump` and `traceroute` are already part of macOS:
```bash
brew install nmap telnet tmux
brew install --cask wireshark
```
`ncat` is part of the `nmap` package.

**Linux (Ubuntu/Debian) and WSL**
```bash
sudo apt update
sudo apt install curl netcat-openbsd ncat telnet dnsutils tcpdump traceroute tmux wireshark
```
`dig` and `host` are part of `dnsutils`. On WSL, install Wireshark on Windows instead ([wireshark.org](https://www.wireshark.org/download.html)): it sees the real network cards of the PC.

Then run `setup_env.sh` again: every line should be `[ok]`.

---

## Common problems

**`conda: command not found`.** The installer did not initialize your shell, or the terminal is still the old one. Open a new terminal. If it still fails, run `~/miniconda3/bin/conda init` followed by the name of your shell (`zsh` on macOS, `bash` on Linux and WSL), then open a new terminal.

**`python` is not 3.11, or `No module named 'hypercorn'`.** The environment is not active in this terminal (or in this tmux pane): run `conda activate reti_calcolatori`.

**`CondaToSNonInteractiveError` during Step 3.** Recent versions of conda ask you to accept the Terms of Service of the Anaconda channels once. Accept them and run Step 3 again:
```bash
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
```

**`EnvironmentNameNotFound: reti_calcolatori`.** The environment was never created: run Step 3.

**I want to start from scratch.** Remove the environment and create it again:
```bash
conda deactivate
conda env remove -n reti_calcolatori
bash 00_PYTHON_ENVIRONMENT_SETUP/setup_env.sh
```

More on conda: [getting started with conda](https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html).
