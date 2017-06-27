#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 26 15:23:05 2017

@author: josepheddy
"""

from urllib.request import urlopen
from bs4 import BeautifulSoup

import pandas as pd

master_url = 'http://web.mta.info/developers/turnstile.html'
master_page = urlopen(master_url)
soup = BeautifulSoup(master_page, 'html.parser', from_encoding='utf-8') 

link_htmls = soup.find_all('a')
url_list = []
for link in link_htmls:
    try:
        url_list += [link['href']]
    except:
        continue

start = url_list.index('resources/nyct/turnstile/Remote-Booth-Station.xls') + 1
end =  url_list.index('data/nyct/turnstile/turnstile_141011.txt')                      

url_list = url_list[start:end]
url_list = ['http://web.mta.info/developers/' + rest for rest in url_list]

url_list_spring = [url for url in url_list if url[url.find('_')+1:][2:4] in ['03','04','05']]

df_MTA = pd.read_csv(url_list_spring[0])

for i in range(1,len(url_list_spring[1:])):
    df_temp = pd.read_csv(url_list_spring[i]) 
    df_MTA = pd.concat([df_MTA, df_temp],ignore_index=True)
    if i % 5 == 0:
        print(i)

df_MTA.to_csv('MTA_Turnstile_Spring.csv', index=False)