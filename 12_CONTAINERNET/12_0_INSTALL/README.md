# Containernet su Ubuntu 26.04

Guida all'installazione di [Containernet](https://containernet.github.io/) su **Ubuntu 26.04 LTS**, con una patch per il supporto a 26.04 e un ambiente **conda**.

## Requisiti

- Ubuntu 26.04 LTS (va bene anche la versione Server), con un utente che può usare `sudo`
- almeno 2 CPU, 4 GB di RAM e 30 GB di disco
- [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install/linux-install): scegli l'installer per la tua architettura (`x86_64` o `aarch64`, la vedi con `uname -m`)

> **Licenza:** i canali predefiniti di Anaconda sono soggetti ai [Terms of Service di Anaconda](https://www.anaconda.com/legal/terms/terms-of-service). Se non potete accettarli, al passo 4 aggiungi `-c conda-forge --override-channels` a `conda create`.

## Installazione

Tutti i comandi partono dalla stessa cartella, per esempio la tua home.

### 1. Pacchetti di base

```bash
sudo apt-get update
sudo apt-get install -y git ansible
```

### 2. Scaricare Containernet e applicare la patch

```bash
git clone https://github.com/containernet/containernet.git
git clone https://github.com/fabriziogiuliano/reti_calcolatori.git

cd containernet
git checkout 8e0aabef8f23def3961b30897dd486191d9bd693
git apply --check ../reti_calcolatori/12_CONTAINERNET/12_0_INSTALL/containernet-ubuntu-26.04.patch
git apply ../reti_calcolatori/12_CONTAINERNET/12_0_INSTALL/containernet-ubuntu-26.04.patch
cd ..
```

La patch vale solo per il commit indicato nel `git checkout`. Se `git apply --check` dà errore, controlla di aver fatto il checkout e non proseguire.

### 3. Installare le dipendenze con Ansible

```bash
sudo ansible-playbook -i "localhost," -c local containernet/ansible/install.yml
```

Installa Docker CE, Open vSwitch, le dipendenze di Mininet e il controller OpenFlow. Ci vogliono diversi minuti.

Se si interrompe e devi rilanciarlo, cancella prima la cartella creata dall'installer: `sudo rm -rf openflow`.

### 4. Ambiente conda

```bash
conda create -n containernet python=3.12 -y
conda activate containernet

cd containernet
pip install .
```

### 5. Verifica

```bash
sudo "$CONDA_PREFIX/bin/python" examples/containernet_example.py
```

Deve comparire `*** Results: 0% dropped (2/2 received)`. Al prompt `containernet>` scrivi `exit`.

Gli script si lanciano sempre con `sudo "$CONDA_PREFIX/bin/python"`, con l'ambiente `containernet` attivo.
