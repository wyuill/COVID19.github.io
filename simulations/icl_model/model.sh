#!/bin/bash -l

DATADIR=/home/patrick/COVID19.github.io/simulations/icl_model/data/
COUNTRIES="Austria,Belgium,Denmark,France,Germany,Italy,Norway,Spain,Sweden,Switzerland,United_Kingdom"
STAN_MODEL=/home/patrick/COVID19.github.io/simulations/icl_model/base.stan
DTS=84 #Days to simulate
ED=2020-03-29 #End date, up to which to include data (different depending on forecast)
OUTDIR=/home/patrick/COVID19.github.io/simulations/icl_model/model_output/3_week_forecast/
/home/patrick/COVID19.github.io/simulations/icl_model/icl_model.py --datadir $DATADIR --countries $COUNTRIES --stan_model $STAN_MODEL --days_to_simulate $DTS --end_date $ED --outdir $OUTDIR
