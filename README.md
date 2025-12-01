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
where `<dirname>` is the directory where the virtual environment is installed.

Original test run
---
This is the original test run, nothing changed. It is given here just for reference; can be skipped.
```
cd picas_cortex/code
sbatch ddcal.sh
```
If finished successfully, there should be output in `outdir`. Note: currently does not work under user's home. Hence, run it under `/project/lofarvwf/Public`.


Run with PiCaS
---

### Create views

If you start with an empty DB, you first need to create views. Standard views ("Monitor") are created with:
```
cd picas_cortex/code 
python create_views.py
```
For this PoC, we also need additional views for specific workflows ("ddcal" and "imaging"), Create these with:
```
python create_views.py workflows
```


###  Create tokens

First create inputfile `tokensfile.txt`. There will be a token generated for each line. 
The line gives the directory with the observation to be processed. 
For example, for the test run:
```
cd picas_cortex/code
echo "/project/lofarvwf/Public/jdejong/picas_test/msdata" > tokensfile.txt
```
To connect to the PiCaS database (DB), you need to have a `picasconfig.py` with your credentials.
You can copy "picasconfig_template.py" and fill it in. IMPORTANT: if you are running in a shared or public directory, make sure you change the permissions of picasconfig.py so that it is not readable by others!

```
chmod 700 picasconfig.py
```

Now create the tokens and store them in the DB with:
```
python push_tokens.py ddcal tokensfile.txt
```
Go to the DB (https://picas.grid.sara.nl:6984/_utils/) and check if the tokens were created succesfully.

### Run Jobs
Via slurm scheduler:
```
sbatch slurm_ddcal.sh
```
The script sets up the environment and runs the pilot job `pilot.py`. The pilot job makes connection the PiCaS DB, 
fetches a "todo" token and starts processing, i.e. running the `master_ddcal.sh`, which is just a slight adaptation of `ddcal.sh`.


For testing, you can also run the pilot job directly on the UI (not recommended as the job takes hours):
```
python pilot.py ddcal
```