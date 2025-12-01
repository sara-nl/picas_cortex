#!/bin/bash


MSDATA=$1   #/project/lofarvwf/Public/jdejong/picas_test/msdata
BIND_DIR=$2 #/project/lofarvwf/Public
SIMG=$3     #/project/lofarvwf/Public/jdejong/picas_test/test_sep_2025.sif
SOLS=$4     #$(realpath outdir/merged.h5)

mkdir -p imaging_output
cd imaging_output
OUTDIR=${PWD}

singularity exec -B $BIND_DIR ${SIMG} \
DP3 \
msin=$MSDATA/*.ms \
msout=${TMPDIR}/concat.ms \
steps=[avg,bdaaverager] \
avg.type=averager \
avg.timestep=8 \
avg.freqstep=8 \
msout.storagemanager='dysco' \
bdaaverager.timebase=70e3 \
bdaaverager.maxinterval=32

singularity exec -B $BIND_DIR ${SIMG} \
ds9facetgenerator \
--ms ${TMPDIR}/concat.ms \
--imsize 25000 \
--pixelscale 0.4 \
--DS9regionout facets.reg \
--h5 ${SOLS}

cp facets.reg ${TMPDIR}
cp ${SOLS} ${TMPDIR}
cd ${TMPDIR}

singularity exec -B /project/lofarvwf/Public ${SIMG} \
wsclean \
-update-model-required \
-gridder wgridder \
-minuv-l 80.0 \
-size 22500 22500 \
-weighting-rank-filter 3 \
-reorder \
-weight briggs -1.5 \
-parallel-reordering 6 \
-mgain 0.75 \
-data-column DATA \
-auto-mask 2.5 \
-auto-threshold 1.0 \
-pol i \
-name 1.2image \
-scale 0.4arcsec \
-taper-gaussian 1.2asec \
-niter 2000000 \
-log-time \
-multiscale-scale-bias 0.7 \
-parallel-deconvolution 2600 \
-multiscale \
-multiscale-max-scales 9 \
-nmiter 6 \
-facet-regions facets.reg \
-apply-facet-solutions merged.h5 amplitude000,phase000 \
-parallel-gridding 6 \
-apply-facet-beam \
-facet-beam-update 600 \
-use-differential-lofar-beam \
-channels-out 12 \
-join-channels \
-fit-spectral-pol 9 \
-local-rms -local-rms-window 50 \
-scalar-visibilities \
-dd-psf-grid 3 3 \
concat.ms

cp *MFS*.fits ${OUTDIR}
