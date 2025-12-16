PoC: PiCaS for CORTEX-lofarvwf (WIP)
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
This is the original test run, nothing changed. It is given here just for reference; it can be skipped.
```
cd picas_cortex/code
sbatch ddcal.sh
```
If finished successfully, there should be output in `outdir`. Note: currently does not work under user's home due to permission issues. Hence, run it under `/project/lofarvwf/Public`.


Run with PiCaS
---

### Create views

If you start with an empty DB, you first need to create views. Standard views ("Monitor") are created with:
```
cd picas_cortex/code 
python create_views.py
```
For this PoC, we also need additional views for specific workflows ("ddcal" and "imaging"). Create these with:
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
Submit pilot job via slurm scheduler:
```
sbatch slurm_ddcal.sh
```
The script sets up the environment and runs the pilot job `pilot.py`. The pilot job makes connection the PiCaS DB, 
fetches a "ddcal/todo" token and starts processing, i.e. running the `master_ddcal.sh`, which is just a slight adaptation of `ddcal.sh`.

If the `ddcal` token is processed successfully, an `imaging` token will be created by `pilot.py`. The new token appears in the "imaging/todo" view and needs `imaging` pilot job to process it, which can be submitted with:
```
sbatch slurm_imaging.sh
```
For convenience this comand has been added to `slurm_ddcal.sh`, so that imaging pilot job automatically starts after the ddcal pilot job.
Currently, the scripts `master_ddcal.sh` and `master_imaging.sh` have been adapted for quick testing to illustrate how the tokens are used. See comments with "quick testing" in the scripts, to revert to full, long runs.

Note that for testing, you can also run pilot jobs directly on the UI (not recommended as the job takes hours), instead of submitting it to SLURM:
```
python pilot.py ddcal
```