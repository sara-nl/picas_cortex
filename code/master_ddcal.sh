#!/bin/bash

######################
######## INPUT #######
######################

# Use the DB to store information for reference (paths to software etc.)
MSDATA=$1 #/project/lofarvwf/Public/jdejong/picas_test/msdata
SING_BIND=$2 #'/project/lofarvwf/'
SIMG_ORIGINAL=$3 #/project/lofarvwf/Public/jdejong/picas_test/test_sep_2025.sif
CAT=$4 #/project/lofarvwf/Public/jdejong/picas_test/final_dd_selection.csv
REPO=$5 #https://git.astron.nl/RD/VLBI-cwl.git
SUBMODS=$6 #/project/lofarvwf/Software/lofar_facet_selfcal/submods


export TOIL_SLURM_ARGS="--export=ALL -t 12:00:00"
######################
######################

# SETUP ENVIRONMENT

mkdir -p software
cd software
git clone $REPO VLBI_cwl
cd ../

# set up singularity
SIMG=vlbi-cwl.sif
export CACHEDIR=singularity_cache
mkdir -p $CACHEDIR
cp $SIMG_ORIGINAL $CACHEDIR/$SIMG
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
export APPTAINERENV_PYTHONPATH=$SUBMODS:$VLBI_DATA_ROOT/scripts:\$PYTHONPATH
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
