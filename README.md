PoC CORTEX-lofarvwf with PiCaS (WIP)
====

Install
---
Clone this repo:
```
git clone git@github.com:sara-nl/picas_cortex.git
```
Install dependencies in a virtual environment, for example:

```
python3 -m virtualenv <dirname>/venv
source <dirname>/venv/bin/activate
pip install -r requirements.txt
```
where <dirname> is the directory for the virtual environment.

Initial test run
---
```
cd picas_cortex/jobs
sbatch ddcal.sh
```


Create tokens
---
First create inputfile `tokensfile.txt` and `input.json`.

```
cd picas_cortex/tokens
python push_tokens.py tokensfile.txt input.json
```

Run Jobs
---
Directly:
```
cd picas_cortex/jobs
python pilot.py ddcal
```

Via slurm scheduler:
``
sbatch slurm_ddcal.sh
``
