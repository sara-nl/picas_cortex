#!/bin/bash
#SBATCH --output=imaging_%j.out
#SBATCH --error=imaging_%j.err
#SBATCH -c 16 -t 96:00:00

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

# Set environmental variables needed in the SLURM job,
# and/or activate virtual environnment:
source .venv/bin/activate

# Use local scratch storage for faster I/O (does not work because toil-jobs need access)
#workdir="$TMPDIR"
workdir="$PWD"

# make a separate directory for each observation (master toil-job)
mkdir "$workdir"/imaging_${SLURM_JOB_ID}

# copy code and config files to scratch dir
script_dir="$PWD"
cp ${script_dir}/*.py ${workdir}/imaging_${SLURM_JOB_ID}/.
cp ${script_dir}/*.sh ${workdir}/imaging_${SLURM_JOB_ID}/.
cd ${workdir}/imaging_${SLURM_JOB_ID}


# Run pilot job
python pilot.py "imaging"

deactivate
