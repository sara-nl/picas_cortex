#!/bin/bash
#SBATCH --output=ddcal_%j.out
#SBATCH --error=ddcal_%j.err


#@helpdesk: SURF helpdesk <helpdesk@surf.nl>
#
#usage: sbatch slurm_ddcal.sh
#description:
#    Connect to PiCaS server
#    Get the next token in todo View
#    Fetch the token parameters, e.g. input value
#    Run main job (process_task.sh) with the input argument
#    When done, return the exit code to the token
#    Attach the logs to the token

echo "Start timestamp: $(date)"

# Use local scratch storage for faster I/O (does not work because toil-jobs need access)
#workdir="$TMPDIR"
workdir="$PWD"

# make a separate directory for each observation (master toil-job)
mkdir "$workdir"/ddcal_${SLURM_JOB_ID}

# copy code and config files to scratch dir
script_dir="$PWD"
cp ${script_dir}/*.py ${workdir}/ddcal_${SLURM_JOB_ID}/.
cp ${script_dir}/*.sh ${workdir}/ddcal_${SLURM_JOB_ID}/.
cd ${workdir}/ddcal_${SLURM_JOB_ID}

# You may set environmental variables needed in the SLURM job or load them from a script:
source /project/lofarvwf/Public/hhu/venv/bin/activate

# Run pilot job
python pilot.py "ddcal"

deactivate
