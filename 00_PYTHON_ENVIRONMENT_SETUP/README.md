# 00 Python environment setup

Every lab of the course runs in the same conda environment, `reti_calcolatori`: Python 3.11 plus the few libraries the labs need (hypercorn for HTTP/2, aiosmtpd for the mail server). Set it up once, at the beginning of the course, and activate it every time you open a terminal.

The course runs on **Ubuntu 26.04 LTS**.

## Files

| File | What it is |
|---|---|
| `setup_env.sh` | Creates the environment, installs the Python packages and checks the command-line tools |
| `requirements.txt` | The Python packages installed by `setup_env.sh` |

---

## Step 1. Install conda

Skip this step if `conda --version` already prints a version (a full Anaconda is fine too).

We use [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install), the minimal installer of conda: only conda and Python, everything else is installed when needed.

**1. Download the installer** into your home folder. `$(uname -m)` picks the right version for your processor by itself (`x86_64` or `aarch64`):
```bash
cd ~
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-$(uname -m).sh
```

**2. Run it** (no `sudo`: conda is installed in your home folder, only for your user):
```bash
bash Miniconda3-latest-Linux-$(uname -m).sh
```

The installer asks four questions. Answer like this:

| The installer shows | You type |
|---|---|
| `Please, press ENTER to continue` | Enter. The license appears: press Space to scroll it to the end (or `q` to skip it) |
| `Do you accept the license terms? [yes\|no]` | `yes` |
| `Miniconda3 will now be installed into this location:`<br>`[/home/<you>/miniconda3] >>>` | Enter, to keep the default folder |
| `Proceed with initialization? [yes\|no]`<br>`[no] >>>` | **`yes`**. The default is `no`: if you just press Enter, conda will not work in new terminals |

At the end it prints `Thank you for installing Miniconda3!`.

**3. Open a new terminal** (close the old one) and check:
```bash
conda --version
```
**Expected output**
```
conda 26.9.4
```
Your version may be different. The prompt now starts with `(base)`: this is conda's default environment, we will not use it.

**4. Accept the Terms of Service of the Anaconda channels.** Recent versions of conda ask for it once, before creating the first environment:
```bash
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
```

**5. Delete the installer**, it is no longer needed:
```bash
rm ~/Miniconda3-latest-Linux-*.sh
```

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
  [missing] telnet   (sudo apt install ...)
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

If Step 3 printed some `[missing]` lines, install the tools:
```bash
sudo apt update
sudo apt install curl netcat-openbsd ncat telnet bind9-dnsutils tcpdump traceroute tmux wireshark
```
`dig` and `host` are part of `bind9-dnsutils`.

Then run `setup_env.sh` again: every line should be `[ok]`.

---

## Common problems

**`conda: command not found`.** The installer did not initialize your shell, or the terminal is still the old one. Open a new terminal. If it still fails, run `~/miniconda3/bin/conda init bash`, then open a new terminal.

**`python` is not 3.11, or `No module named 'hypercorn'`.** The environment is not active in this terminal (or in this tmux pane): run `conda activate reti_calcolatori`.

**`CondaToSNonInteractiveError` during Step 3.** The Terms of Service of the Anaconda channels were not accepted: run point 4 of Step 1, then Step 3 again.

**`EnvironmentNameNotFound: reti_calcolatori`.** The environment was never created: run Step 3.

**I want to start from scratch.** Remove the environment and create it again:
```bash
conda deactivate
conda env remove -n reti_calcolatori
bash 00_PYTHON_ENVIRONMENT_SETUP/setup_env.sh
```

More on conda: [getting started with conda](https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html).
