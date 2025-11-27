#!/bin/bash
#SBATCH --output=ddcal_%j.out
#SBATCH --error=ddcal_%j.err
#SBATCH -p infinite

######################
######## INPUT #######
######################

VENV=/project/lofarvwf/Public/jdejong/cloudbursting/ddcaltest7.0.0/venv
CAT=/project/lofarvwf/Public/jdejong/picas_test/final_dd_selection.csv
MSDATA=/project/lofarvwf/Public/jdejong/picas_test/msdata

export TOIL_SLURM_ARGS="--export=ALL -t 12:00:00"
SING_BIND="/project/lofarvwf/"

######################
######################

# SETUP ENVIRONMENT

# set up software
source ${VENV}/bin/activate

mkdir -p software
cd software
git clone https://git.astron.nl/RD/VLBI-cwl.git VLBI_cwl
cd ../

# set up singularity
SIMG=vlbi-cwl.sif
export CACHEDIR=singularity_cache
mkdir -p $CACHEDIR
cp /project/lofarvwf/Public/jdejong/picas_test/test_sep_2025.sif $CACHEDIR/$SIMG
mkdir -p $CACHEDIR/pull
cp $CACHEDIR/$SIMG $CACHEDIR/pull/vlbi-cwl.sif
chmod 755 -R $CACHEDIR

# set up environment variables
export VLBI_DATA_ROOT=$PWD/software/VLBI_cwl
export APPTAINER_CACHEDIR=$PWD/$CACHEDIR
export APPTAINER_PULLDIR=${APPTAINER_CACHEDIR}/pull
export APPTAINER_TMPDIR=${APPTAINER_CACHEDIR}/tmp
export CWL_SINGULARITY_CACHE=$APPTAINER_CACHEDIR
export APPTAINERENV_VLBI_DATA_ROOT=$VLBI_DATA_ROOT
export APPTAINERENV_PREPEND_PATH=$VLBI_DATA_ROOT/scripts
export APPTAINERENV_PYTHONPATH=/project/lofarvwf/Software/lofar_facet_selfcal/submods:$VLBI_DATA_ROOT/scripts:\$PYTHONPATH
export APPTAINER_BIND=$SING_BIND
export TOIL_CHECK_ENV=True

########################

# Make JSON file
JSON="input.json"

# Add MS
json="{\"msin\":["
for file in "$MSDATA"/*.ms; do
    json="$json{\"class\": \"Directory\", \"path\": \"$file\"},"
done
json="${json%,}]}"
echo "$json" > "$JSON"

# Add source_catalogue file
jq --arg path "$CAT" \
   '. + {
     "source_catalogue": {
       "class": "File",
       "path": $path
     }
   }' "$JSON" > temp.json && mv temp.json "$JSON"

jq --arg path "$CAT" \
   '. + {
     "custom_phasediff_score_csv": {
       "class": "File",
       "path": $path
     }
   }' "$JSON" > temp.json && mv temp.json "$JSON"


NNCACHE=$PWD/nn_cache
singularity exec $CACHEDIR/vlbi-cwl.sif download_NN --cache_directory $NNCACHE
jq --arg NNCACHE "$NNCACHE" '. + {model_cache: $NNCACHE}' "$JSON" > temp.json && mv temp.json "$JSON"

SELECTION=false
jq --argjson SELECTION "$SELECTION" '. + {dd_selection: $SELECTION}' "$JSON" > temp.json && mv temp.json "$JSON"

########################

# Make folders for running toil
WORKDIR=$PWD/workdir
OUTPUT=$PWD/outdir
JOBSTORE=$PWD/jobstore
LOGDIR=$PWD/logs
TMPD=$PWD/tmpdir

mkdir -p $WORKDIR
mkdir -p $OUTPUT
mkdir -p $LOGDIR

########################

# RUN TOIL

toil-cwl-runner \
--no-read-only \
--retryCount 2 \
--singularity \
--disableCaching \
--logFile full_log.log \
--writeLogs ${LOGDIR} \
--outdir ${OUTPUT} \
--tmp-outdir-prefix ${TMPD}/ \
--jobStore ${JOBSTORE} \
--workDir ${WORKDIR} \
--disableAutoDeployment True \
--bypass-file-store \
--cleanWorkDir onSuccess \
--eval-timeout 4000 \
--preserve-environment ${APPTAINERENV_PYTHONPATH} ${APPTAINER_BIND} ${APPTAINER_PULLDIR} ${APPTAINER_CACHEDIR} \
--batchSystem=slurm \
software/VLBI_cwl/workflows/dd-calibration.cwl input.json

########################

deactivate
