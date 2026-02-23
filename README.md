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
cd picas_cortex
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
where `<dirname>` is the directory where the virtual environment is installed.

Original test run
---
This is the original test run, nothing changed. It is given here just for reference; it can be skipped.
```
cd src
sbatch ddcal.sh
```
If finished successfully, there should be output in `outdir`. Note: currently does not work under user's home due to permission issues. Hence, run it under `/project/lofarvwf/Public`.


Run with PiCaS
---

### Create config file
To be able to connect to the PiCaS database (DB), you need a configuration file ` ~/.config/picas/conf.yml` with your credentials. The config file is created with:
```
cd src
python create_config.py
```
You will be asked to enter your account details. The password is stored encrypted.


### Create views

If you start with an empty DB, you first need to create views. Standard views ("Monitor") are created with:
```
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
echo "/project/lofarvwf/Public/jdejong/picas_test/msdata" > tokensfile.txt
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

If the `ddcal` token is processed successfully, an `imaging` token will be created by `pilot.py`. The new token appears in the "imaging/todo" view and needs an `imaging` pilot job to process it, which can be submitted with:
```
sbatch slurm_imaging.sh
```
For convenience the above command is called in `slurm_ddcal.sh` after the `ddcal` pilot job finishes. This ensures that the `imaging` pilot job starts automatically after the `ddcal` pilot job. In real workflows, this could be done via scron jobs that continuously check if there is work to do (tokens to process).

The scripts `master_ddcal.sh` and `master_imaging.sh` have been adapted for quick testing to illustrate how the PoC works with PiCaS tokens, without doing the actual computations. See comments with "quick testing" in the scripts, to revert to full processing runs.