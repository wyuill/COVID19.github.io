#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import sys
import os
import glob
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
import numpy as np
import seaborn as sns
import pystan

import pdb



#Arguments for argparse module:
parser = argparse.ArgumentParser(description = '''Visuaize results from leave one out analysis of model using google mobility data and most of the ICL response team model. The script compares the means for all countries in all leave one out analyses.''')

parser.add_argument('--datadir', nargs=1, type= str, default=sys.stdin, help = 'Path to outdir.')
parser.add_argument('--country_combos', nargs=1, type= str, default=sys.stdin, help = 'Country combinations modeled in leave one out analysis (csv).')
parser.add_argument('--days_to_simulate', nargs=1, type= int, default=sys.stdin, help = 'Number of days to simulate.')
parser.add_argument('--outdir', nargs=1, type= str, default=sys.stdin, help = 'Path to outdir.')

def read_and_format_data(datadir, country, days_to_simulate):
        '''Read in and format all data needed for the model
        '''

        #Get epidemic data
        epidemic_data = pd.read_csv(datadir+'ecdc_20200412.csv')
        #Convert to datetime
        epidemic_data['dateRep'] = pd.to_datetime(epidemic_data['dateRep'], format='%d/%m/%Y')

        #Model data - to be used for plotting
        stan_data = {'dates_by_country':np.zeros(days_to_simulate, dtype='datetime64[D]'),
             'deaths_by_country':np.zeros(days_to_simulate),
             'cases_by_country':np.zeros(days_to_simulate),
             'days_by_country':0
              }


        #Covariate names
        covariate_names = ['retail','grocery','transit','work','residential']
        #Get data by country
        #Get country epidemic data
        country_epidemic_data = epidemic_data[epidemic_data['countriesAndTerritories']==country]
        #Sort on date
        country_epidemic_data = country_epidemic_data.sort_values(by='dateRep')
        #Reset index
        country_epidemic_data = country_epidemic_data.reset_index()
        #Get all dates with at least 10 deaths
        cum_deaths = country_epidemic_data['deaths'].cumsum()
        death_index = cum_deaths[cum_deaths>=10].index[0]
        di30 = death_index-30
        #Get part of country_epidemic_data 30 days before day with at least 10 deaths
        country_epidemic_data = country_epidemic_data.loc[di30:]
        #Reset index
        country_epidemic_data = country_epidemic_data.reset_index()

        print(country, len(country_epidemic_data))
        #Check that foreacast is really a forecast
        N = len(country_epidemic_data)
        stan_data['days_by_country']=N
        forecast = days_to_simulate - N
        if forecast <0: #If the number of predicted days are less than the number available
            days_to_simulate = N
            forecast = 0
            print('Forecast error!')
            pdb.set_trace()

        #Save dates
        stan_data['dates_by_country'][:N] = np.array(country_epidemic_data['dateRep'], dtype='datetime64[D]')
        #Save deaths
        stan_data['deaths_by_country'][:N] = country_epidemic_data['deaths']
        #Save cases
        stan_data['cases_by_country'][:N] = country_epidemic_data['cases']

        return stan_data

def visualize_results(outdir, country_combos, country_data, all_countries, days_to_simulate):
    '''Visualize results by reading in all information from all countries in all combinations
    of the leave one out analysis.
    '''
    #Get all data from all simulations for each country
    country_means = {"Austria":np.zeros((3,10,days_to_simulate)), #Cases,Deaths,Rt for all combinations and all days  
                     "Belgium":np.zeros((3,10,days_to_simulate)),
                     "Denmark":np.zeros((3,10,days_to_simulate)),
                     "France":np.zeros((3,10,days_to_simulate)),
                     "Germany":np.zeros((3,10,days_to_simulate)),
                     "Italy":np.zeros((3,10,days_to_simulate)),  
                     "Norway":np.zeros((3,10,days_to_simulate)), 
                     "Spain":np.zeros((3,10,days_to_simulate)), 
                     "Sweden":np.zeros((3,10,days_to_simulate)), 
                     "Switzerland":np.zeros((3,10,days_to_simulate)), 
                     "United_Kingdom":np.zeros((3,10,days_to_simulate))
                    }
    
    alpha_per_combo = np.zeros((3,6,11)) #mean,2.5 and 97.5 values (95 % CI together)
    #Loop through all country combos
    fetched_combos = {"Austria":0,"Belgium":0,"Denmark":0,"France":0, #Keep track of index for each country
                      "Germany":0,"Italy":0,"Norway":0,"Spain":0,
                      "Sweden":0,"Switzerland":0,"United_Kingdom":0} 
    for i in range(len(country_combos)):
        countries = country_combos.loc[i].values
        summary = pd.read_csv(outdir+'COMBO'+str(i+1)+'/summary.csv')
        #Get alphas
        for a in range(5):
            alpha = summary[summary['Unnamed: 0']=='alpha['+str(a+1)+']']
            alpha_m = 1-np.exp(-alpha['mean'].values[0])
            alpha_2_5 = 1-np.exp(-alpha['2.5%'].values[0])
            alpha_97_5 = 1-np.exp(-alpha['97.5%'].values[0]) 
            alpha_per_combo[0,a,i]=alpha_m #Save mean
            alpha_per_combo[1,a,i]=alpha_2_5 #Save mean
            alpha_per_combo[2,a,i]=alpha_97_5 #Save mean
        #Loop through all countries in combo
        for j in range(len(countries)):
            country= countries[j]
            #Extract mean modeling results for country j
            means = {'prediction':[],'E_deaths':[], 'Rt':[]}
            for k in range(1,days_to_simulate+1):
                for var in ['prediction', 'E_deaths', 'Rt']:
                    var_ij = summary[summary['Unnamed: 0']==var+'['+str(k)+','+str(j+1)+']']
                    means[var].append(var_ij['mean'].values[0])
            #Save data to country means
            country_means[country][0,fetched_combos[country],:]=means['prediction']
            country_means[country][1,fetched_combos[country],:]=means['E_deaths']
            country_means[country][2,fetched_combos[country],:]=means['Rt']
            fetched_combos[country]+=1 #Increase location index in np array


    #Plot alphas - influence of each mobility parameter
    covariate_names = ['retail and recreation','grocery and pharmacy', 'transit stations','workplace','residential']
    alpha_colors = {0:'tab:blue',1:'tab:orange',2:'tab:green', 3:'tab:red', 4:'tab:purple'}
    for i in range(5): #Loop through all mobility params
        fig, ax = plt.subplots(figsize=(4, 4))
        for j in range(11):
            lo_country = all_countries[i] #Left out country
            ax.scatter(j+1,alpha_per_combo[0,i,j], marker="_", color = alpha_colors[i]) #plot mean
            ax.plot([j+1]*2,alpha_per_combo[1:,i,j], color = alpha_colors[i]) #plot 2.5
            ax.set_ylim([0,1])
            ax.set_ylabel('Fractional reduction in R0')
            ax.set_xticks(np.arange(1,12))
            ax.set_xticklabels(all_countries,rotation='vertical')
            ax.set_title(covariate_names[i])
            fig.tight_layout()
            fig.savefig(outdir+'LOO/plots/'+covariate_names[i]+'.png', format='png')
            plt.close()


    #plot per country
    days = np.arange(0,days_to_simulate) #Days to simulate
    for country in country_means:
        means = country_means[country]
        data = country_data[country]
        dates = data['dates_by_country']
        observed_country_deaths = data['deaths_by_country']
        observed_country_cases = data['cases_by_country']
        end = data['days_by_country']#End of data for country i

        #Plot cases
        #Per day
       
        plot_shade_ci(days, end, dates[0], means[0,:,:], observed_country_cases, 'Cases per day',
        outdir+'LOO/plots/'+country+'_cases.png')
        #Cumulative
        plot_shade_ci(days, end, dates[0], np.cumsum(np.array(means[0,:,:],dtype='int16'),axis=1), np.cumsum(observed_country_cases),
        'Cumulative cases',outdir+'LOO/plots/'+country+'_cumulative_cases.png')
        #Plot Deaths
        plot_shade_ci(days, end, dates[0],means[1,:,:],observed_country_deaths,'Deaths per day',
        outdir+'LOO/plots/'+country+'_deaths.png')
        #Plot R
        plot_shade_ci(days, end, dates[0],means[2,:,:],'','Rt',outdir+'LOO/plots/'+country+'_Rt.png')
        #Correlations
        print(country+','+'Rt'+','+str(np.average(np.corrcoef(means[2,:,:])[0,1:])))

    return None


def plot_shade_ci(x,end,start_date,y, observed_y, ylabel, outname):
    '''Plot with shaded 95 % CI (plots both 1 and 2 std, where 2 = 95 % interval)
    '''
    dates = np.arange(start_date,np.datetime64('2020-04-20')) #Get dates - increase for longer foreacast
    forecast = len(dates)
    fig, ax = plt.subplots(figsize=(9, 4))
    #Plot observed dates
    if len(observed_y)>1:
        ax.bar(x[:end],observed_y[:end], alpha = 0.5)
    #Plot the mean for each LOO combo
    for i in range(10): 
        #Plot so far
        ax.plot(x[:end],y[i,:end], alpha=0.5, color='b', linewidth = 1.0)
        #Plot predicted dates
        ax.plot(x[end-1:forecast],y[i,end-1:forecast], alpha=0.5, color='g', linewidth = 1.0)
   
    #Format axis
    ax.set_ylabel(ylabel)
    ax.set_ylim([0,np.amax(y[:,:forecast])])
    xticks=np.arange(forecast-1,0,-7)
    ax.set_xticks(xticks)
    ax.set_xticklabels(dates[xticks],rotation='vertical')
    fig.tight_layout()
    fig.savefig(outname, format = 'png')
    plt.close()



#####MAIN#####
args = parser.parse_args()
datadir = args.datadir[0]
country_combos = pd.read_csv(args.country_combos[0], header = None)
days_to_simulate=args.days_to_simulate[0] #Number of days to model. Increase for further forecast
outdir = args.outdir[0]

#Get data per country
country_data = {} #Save all data from all extracted country combinations
all_countries = ["Austria", "Belgium", "Denmark", "France", "Germany", "Italy", "Norway", "Spain", "Sweden", "Switzerland", "United_Kingdom"]
for country in all_countries:
    #Read data
    stan_data = read_and_format_data(datadir, country, days_to_simulate)
    country_data[country]=stan_data

#Visualize
visualize_results(outdir, country_combos, country_data, all_countries, days_to_simulate)
