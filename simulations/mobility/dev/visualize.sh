#!/bin/bash -l

DATADIR=../data/
OUTDIR=../model_output/R0_2_79/dev/
COUNTRIES="Sweden" #Make sure these are in the same order as when simulating!
DTS=69
SD=$OUTDIR'/plots/short_dates.csv'
#Visualize model output
./visualize_model_output.py --datadir $DATADIR --countries $COUNTRIES --days_to_simulate $DTS --short_dates $SD --outdir $OUTDIR
