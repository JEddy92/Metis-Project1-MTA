#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 27 16:29:01 2017

@author: josepheddy
"""
import pandas as pd
import numpy as np
from scipy.stats import zscore

import datetime
import dateutil.parser

import matplotlib.pyplot as plt
import seaborn as sns

'''SETUP'''
#Load and setup the turnstile dataframe - the data used here is 2015-2017 March-May data
#pulled directly from the MTA's turnstile data files
df_MTA = pd.read_csv('MTA_Turnstile_Spring.csv')
df_MTA.columns = df_MTA.columns.str.strip()

#Reformat date and create day of week column, standardize some station names
df_MTA['DATE'] = [dateutil.parser.parse(date) for date in df_MTA['DATE']]
df_MTA['DAY_OF_WEEK'] = [datetime.datetime.weekday(date) for date in df_MTA['DATE']]
            
df_MTA.replace({'STATION' : \
               { 'GRD CNTRL-42 ST' : '42 ST-GRD CNTRL', \
                  'TIMES SQ-42 ST' : '42 ST-TIMES SQ', \
                  '42 ST-PA BUS TE' : '42 ST-PORT AUTH', \
                  '59 ST COLUMBUS' : '59 ST-COLUMBUS', \
                  '47-50 STS ROCK' : '47-50 ST-ROCK' }}, inplace=True)

#Kick out some stations with multiple stations under the same name - ideally
#would write a method for deduplicating these but beyond scope of this project 
df_MTA = df_MTA[~df_MTA['STATION'].isin(['23 ST','86 ST'])]

''' DAY LEVEL ANALYSIS:
    
    Aggregating to the daily level per station
'''

#df_MTA_byDate: stores total daily entries per turnstile using groupby, min cumulative counts, 
#and the diff function. We do some cleaning / kick out the unreasonable counts where
#something went wrong with the cumulative tracker in the data.

df_MTA_byDate = df_MTA.groupby(['C/A','UNIT','SCP','STATION','DATE','DAY_OF_WEEK']) \
                .ENTRIES.agg({'MIN_ENTRIES':'min'})
df_MTA_byDate = df_MTA_byDate.reset_index()

df_MTA_byDate['DAILY_ENTRIES'] = df_MTA_byDate.groupby(['C/A','UNIT','SCP','STATION']) \
                                 .MIN_ENTRIES.diff().shift(-1)

df_MTA_byDate.drop('MIN_ENTRIES',axis=1,inplace=True) 
df_MTA_byDate.loc[df_MTA_byDate['DAILY_ENTRIES'] < 0, 'DAILY_ENTRIES'] = np.nan
df_MTA_byDate.loc[df_MTA_byDate['DAILY_ENTRIES'] > 100000, 'DAILY_ENTRIES'] = np.nan
                 
#can't properly compute daily count for final days in each year, so exclude these
df_MTA_byDate = df_MTA_byDate[~df_MTA_byDate['DATE'].isin(['2015-05-29','2016-05-27','2017-05-26'])]

#df_MTA_Stat_Daily: stores total daily entries per Station
df_MTA_Stat_Daily = df_MTA_byDate.reset_index().drop(['C/A','SCP','UNIT'],axis=1)
df_MTA_Stat_Daily = df_MTA_Stat_Daily.groupby(['STATION','DATE','DAY_OF_WEEK']).DAILY_ENTRIES \
                    .agg({'DAILY_ENTRIES':'sum'}) \
                    .reset_index()

#df_MTA_Stat_WkDay: stores avg daily entries by day of the week per Station
df_MTA_Stat_WkDay = df_MTA_Stat_Daily.groupby(['STATION','DAY_OF_WEEK']).DAILY_ENTRIES \
                    .agg({'AVG_DAILY_ENTRIES':'mean','STD_DAILY_ENTRIES':'std'}) \
                    .reset_index()

#df_MTA_Stat_AnyDay: stores avg daily entries for any day of the week per Station,
#sorted in descending order of avg daily entries
df_MTA_Stat_AnyDay = df_MTA_Stat_Daily.groupby(['STATION']).DAILY_ENTRIES \
                    .agg({'AVG_DAILY_ENTRIES':'mean'}) \
                    .reset_index()
                    
df_MTA_Stat_AnyDay = df_MTA_Stat_AnyDay \
                    .sort_values(by='AVG_DAILY_ENTRIES',ascending=False) \
                    .reset_index()
 
#Record station names with the most entry volume                    
Stations_Top10 = df_MTA_Stat_AnyDay['STATION'].values[:10]
Stations_Top6 = df_MTA_Stat_AnyDay['STATION'].values[:6]

#df_MTA_Stat_WkDay_Top10: avg daily by day of week for top 10 stations
#df_MTA_Stat_WkDay_Top6: avg daily by day of week for top 6 stations    
df_MTA_Stat_WkDay_Top10 = df_MTA_Stat_WkDay[df_MTA_Stat_WkDay['STATION'].isin(Stations_Top10)]   
df_MTA_Stat_WkDay_Top6 = df_MTA_Stat_WkDay[df_MTA_Stat_WkDay['STATION'].isin(Stations_Top6)] 

'''Line plot of avg entries +- 1 sdev by day of week for top 6 volume stations
'''

days_list = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

fig, ax = plt.subplots()
labels = []
for station, grp in df_MTA_Stat_WkDay_Top6.groupby(['STATION']):
    ax = grp.plot(ax=ax, kind='line', x='DAY_OF_WEEK', y='AVG_DAILY_ENTRIES')
    labels.append(station)
    plt.fill_between(grp['DAY_OF_WEEK'], \
                     grp['AVG_DAILY_ENTRIES']-grp['STD_DAILY_ENTRIES'], \
                     grp['AVG_DAILY_ENTRIES']+grp['STD_DAILY_ENTRIES'], \
                     alpha=0.5)

box = ax.get_position()
ax.set_position([box.x0, box.y0 + box.height * 0.1,
                 box.width, box.height * 0.9])

ax.legend(labels, ncol=3, loc='upper center', bbox_to_anchor=(0.5, -0.10), \
          fancybox=True, shadow=True)

plt.title('Average Daily Entries +- 1 Standard Deviation By Major Station')
plt.xlabel('Day Of The Week')
plt.ylabel('Average Entries')
plt.xticks(range(7),days_list)
plt.show()

''' Bar plot of avg entries for top 10 volume stations by day of the week
'''
ax = sns.barplot(x='STATION', y='AVG_DAILY_ENTRIES', \
                 hue='DAY_OF_WEEK', hue_order=days_list, \
                 data=df_MTA_Stat_WkDay_Top10 \
                      .replace({'DAY_OF_WEEK' : \
                               {0 : 'Monday', 1 : 'Tuesday', 2 : 'Wednesday', \
                                3 : 'Thursday', 4 : 'Friday', 5 : 'Saturday', 6 : 'Sunday'}}))

plt.title('Average Entries For Major Stations By Day Of The Week')
plt.xlabel('Station')
plt.ylabel('Average Entries')
ax.legend(title='Day Of The Week',ncol=2)
plt.xticks(rotation=60)
plt.show()

'''Dist plot of avg daily entries for top 20 stations
'''
ax = sns.distplot(df_MTA_Stat_AnyDay['AVG_DAILY_ENTRIES'][:20],kde=True)
plt.title('Distribution Of Average Daily Entries For Top 20 Volume Stations')
plt.xlabel('Average Daily Entries')
plt.show()

'''ANALYSIS OF VOLUME VS INCOME METRICS

'''

#pulling in our curated property value and income data for stations in wealthy enough areas
df_StationWealth = pd.read_csv('wealthincome.csv')
df_StationWealth.replace({'STATION' : {'59 ST COLUMBUS' : '59 ST-COLUMBUS'}}, inplace=True)
df_MTA_Stat_AnyDay_Wealth = pd.merge(df_MTA_Stat_AnyDay, df_StationWealth, on='STATION')

'''Joint plots of wealth metrics (% nearby income > 100k, nearby property value)
   vs. average daily entries 
'''
ax = sns.jointplot('AVG_DAILY_ENTRIES', 'PCNTOVER100K', kind='regplot', data=df_MTA_Stat_AnyDay_Wealth)
plt.xlabel('Average Daily Entries')
plt.ylabel('Percent Of Nearby Incomes Over 100K')
plt.show()

ax = sns.jointplot('AVG_DAILY_ENTRIES', 'PROPVAL-M', kind='regplot', data=df_MTA_Stat_AnyDay_Wealth)
plt.xlabel('Average Daily Entries')
plt.ylabel('Nearby Property Value In Millions')
plt.show()

'''Custom Scoring: weighted combination of daily volume, property and income metrics,
   Using Z Scores to standardize scale
'''
df_MTA_Stat_AnyDay_WealthZ = df_MTA_Stat_AnyDay_Wealth 
df_MTA_Stat_AnyDay_WealthZ[['AVG_DAILY_ENTRIES','PROPVAL-M','PCNTOVER100K']] = \
                          df_MTA_Stat_AnyDay_WealthZ[['AVG_DAILY_ENTRIES','PROPVAL-M','PCNTOVER100K']] \
                          .apply(zscore)
                          
Appeal_Scores = [.6 * row['AVG_DAILY_ENTRIES'] + .2 * row['PROPVAL-M'] + .2 * row['PCNTOVER100K'] \
                 for _, row in df_MTA_Stat_AnyDay_WealthZ.iterrows() ]

df_MTA_Stat_AnyDay_WealthZ['APPEAL_SCORE'] = Appeal_Scores 
df_MTA_Stat_AnyDay_WealthZ.sort_values(by='APPEAL_SCORE',ascending=False,inplace=True)   

'''Plotting For The Top 6 Most Appealing
'''

Stations_Top6_Appeal = df_MTA_Stat_AnyDay_WealthZ['STATION'].values[:6]
df_MTA_Stat_WkDay_Top6_Appeal = df_MTA_Stat_WkDay[df_MTA_Stat_WkDay['STATION'].isin(Stations_Top6_Appeal)] 

'''Line plot of avg entries +- 1 sdev by day of week for top 6 appeal scored stations
'''
fig, ax = plt.subplots()
labels = []
for station, grp in df_MTA_Stat_WkDay_Top6_Appeal.groupby(['STATION']):
    ax = grp.plot(ax=ax, kind='line', x='DAY_OF_WEEK', y='AVG_DAILY_ENTRIES')
    labels.append(station)
    plt.fill_between(grp['DAY_OF_WEEK'], \
                     grp['AVG_DAILY_ENTRIES']-grp['STD_DAILY_ENTRIES'], \
                     grp['AVG_DAILY_ENTRIES']+grp['STD_DAILY_ENTRIES'], \
                     alpha=0.5)

box = ax.get_position()
ax.set_position([box.x0, box.y0 + box.height * 0.1,
                 box.width, box.height * 0.9])

ax.legend(labels, ncol=3, loc='upper center', bbox_to_anchor=(0.5, -0.10), \
          fancybox=True, shadow=True)

plt.title('Average Daily Entries +- 1 Standard Deviation By Most Appealing Station')
plt.xlabel('Day Of The Week')
plt.ylabel('Average Entries')
plt.xticks(range(7),days_list)
plt.show()

''' Bar plot of avg entries for top 6 appealing station by day of the week
'''
ax = sns.barplot(x='STATION', y='AVG_DAILY_ENTRIES', \
                 hue='DAY_OF_WEEK', hue_order=days_list, \
                 data=df_MTA_Stat_WkDay_Top6_Appeal \
                      .replace({'DAY_OF_WEEK' : \
                               {0 : 'Monday', 1 : 'Tuesday', 2 : 'Wednesday', \
                                3 : 'Thursday', 4 : 'Friday', 5 : 'Saturday', 6 : 'Sunday'}}))

plt.title('Average Entries For Most Appealing Stations By Day Of The Week')
plt.xlabel('Station')
plt.ylabel('Average Entries')
ax.legend(title='Day Of The Week',ncol=2)
plt.xticks(rotation=60)
plt.show()        
 