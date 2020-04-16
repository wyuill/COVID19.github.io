#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import os
import glob
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


import pdb

#Arguments for argparse module:
parser = argparse.ArgumentParser(description = '''Plot the mobility data for each country in overlay with different NPIs''')

parser.add_argument('--datadir', nargs=1, type= str, default=sys.stdin, help = 'Path to outdir.')
parser.add_argument('--outdir', nargs=1, type= str, default=sys.stdin, help = 'Path to outdir.')



def read_data_and_plot(datadir, countries, geoIds, outdir):
    '''Read in mobility data and dates for NPI and
    generate overlay plots showing the correlation between
    NPIs and mobility patterns.
    '''
    #Covariate names
    covariate_names = ['retail','grocery','transit','work','residential']
    covariate_labels = {'retail':'retail and recreation', 'grocery':'grocery and pharmacy', 'transit':'transit stations','work':'workplace','residential': 'residential'}
    #NPIs
    NPI = ['schools_universities',  'public_events', 'lockdown',
        'social_distancing_encouraged', 'self_isolating_if_ill']

    NPI_labels = {'schools_universities':'schools and universities',  'public_events': 'public events', 'lockdown': 'lockdown',
        'social_distancing_encouraged':'social distancing encouraged', 'self_isolating_if_ill':'self isolating if ill'}
    #Read in intervention dates
    intervention_df = pd.read_csv(datadir+'interventions_only.csv')

    for i in range(len(countries)):
        country = countries[i]
        country_npi = intervention_df[intervention_df['Country']==country]
        geoId = geoIds[i]
        fig, ax = plt.subplots(figsize=(6, 4)) #Figure
        #Plot mobility curves
        for name in covariate_names:
            country_cov_name = pd.read_csv(datadir+'europe/'+geoId+'-'+name+'.csv')
            country_cov_name['Date'] = pd.to_datetime(country_cov_name['Date'])

            ax.plot(np.array(country_cov_name['Date'], dtype="datetime64[D]"), np.array(country_cov_name['Change'], dtype=np.float32), label = covariate_labels[name])

        #Plot NPIs
        y_npi = 0
        for npi in NPI:
            plt.axvline(pd.to_datetime(country_npi[npi].values[0]))
            ax.scatter(pd.to_datetime(country_npi[npi].values[0]), y_npi)
            plt.text(pd.to_datetime(country_npi[npi].values[0]), y_npi, NPI_labels[npi])
            y_npi -= 10
        ax.set_ylabel('Relative Change')
        ax.set_ylim([-100,40])
        plt.legend()
        #X axis foratting
        xtick_labels = np.arange(np.datetime64('2020-02-15'),np.datetime64('2020-03-30')) #Get dates - increase for longer foreacast
        xticks=np.arange(0,len(xtick_labels),7)
        ax.set_xticklabels(xtick_labels[xticks],rotation=90)
        plt.tight_layout()
        pdb.set_trace()

        fig.savefig(outdir+'plots/'+country+'_mobility', format='png')
        plt.close()



#####MAIN#####
args = parser.parse_args()
datadir = args.datadir[0]
outdir = args.outdir[0]
#Read data
countries = ["Denmark", "Italy", "Germany", "Spain", "United_Kingdom", "France", "Norway", "Belgium", "Austria", "Sweden", "Switzerland"]
geoIds = ["DK","IT","DE","ES","UK","FR","NO", "BE", "AT", "SE", "CH"]
read_data_and_plot(datadir, countries, geoIds, outdir)