#!/usr/bin/env bash
# Creates (if missing) the conda env and installs everything the labs need.
# Usage: bash setup_env.sh      then: conda activate reti_calcolatori
set -e

ENV_NAME=reti_calcolatori
PY_VERSION=3.11
cd "$(dirname "$0")"

# 1. Conda env
eval "$(conda shell.bash hook)"
if conda env list | grep -qE "^${ENV_NAME}\s"; then
    echo ">>> Env '$ENV_NAME' already exists"
else
    echo ">>> Creating env '$ENV_NAME' (Python $PY_VERSION)"
    conda create -y -n "$ENV_NAME" python="$PY_VERSION"
fi
conda activate "$ENV_NAME"

# 2. Python packages
echo ">>> Installing Python packages"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 3. Command-line tools used in the READMEs (checked, not installed)
echo ">>> Checking command-line tools"
for tool in curl nc telnet ncat dig host tcpdump traceroute tmux wireshark; do
    if command -v "$tool" >/dev/null 2>&1 || { [ "$tool" = wireshark ] && [ -d /Applications/Wireshark.app ]; }; then
        echo "  [ok]      $tool"
    else
        echo "  [missing] $tool   (macOS: brew install ...  Linux: sudo apt install ...)"
    fi
done

echo ">>> Done. Run: conda activate $ENV_NAME"
