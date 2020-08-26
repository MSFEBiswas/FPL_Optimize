# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 19:51:55 2020

@author: noahk
"""

import requests
import json
import pandas as pd
import numpy as np
import seaborn as sns
import aiohttp
import asyncio
import nest_asyncio
from understat import Understat
from fuzzywuzzy import fuzz,process
import matplotlib


nest_asyncio.apply()

async def all_players():
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        data = await understat.get_league_players("epl", 2019)
        json_ = json.loads((json.dumps(data)))
        return json_

def normalize_to_df(json_data):
    df = pd.io.json.json_normalize(json_data)
    df = df.drop(['id', 'position'], axis = 1)
    return df

def connect_fpl_api():
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    r = requests.get(url)
    json = r.json()
    json.keys()
    
    elements_df = pd.DataFrame(json['elements'])
    elements_types_df = pd.DataFrame(json['element_types'])
    teams_df = pd.DataFrame(json['teams'])
    
    elements_df['position'] = elements_df.element_type.map(elements_types_df.set_index('id').singular_name)
    elements_df['team'] = elements_df.team.map(teams_df.set_index('id').name)
    elements_df['name'] = elements_df['first_name'] + ' ' + elements_df['second_name']
    
    final_df = elements_df[['name','team', 'position','total_points', 'selected_by_percent', 'now_cost',\
                            'minutes', 'transfers_in', 'value_season','goals_scored','assists','clean_sheets',\
                            'creativity','creativity_rank','threat','threat_rank','influence','influence_rank','ict_index',\
                            'ict_index_rank','element_type','penalties_missed','points_per_game',\
                            'bonus','bps']]
    final_df['name'] = final_df['name'].astype(str)
    final_df['team'] = final_df['team'].astype(str)
    final_df['creativity'] = final_df['creativity'].astype(float)
    final_df['threat'] = final_df['threat'].astype(float)
    final_df['ict_index'] = final_df['ict_index'].astype(float)
    final_df['points_per_game'] = final_df['points_per_game'].astype(float)
    final_df['influence'] = final_df['influence'].astype(float)
    final_df['value_season'] = final_df['value_season'].astype(float)
    final_df = final_df.sort_values(by=['value_season'], ascending=False).reset_index(drop=True)
    final_df['value_minutes'] = (final_df['value_season']/final_df['minutes'])*100
    return final_df

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    json_all_players = loop.run_until_complete(all_players())
    player_xStats = normalize_to_df(json_all_players)
    
    fpl_data = connect_fpl_api()
    value_players = fpl_data.sort_values(by=['value_minutes'], ascending=False)
    value_players = value_players.where(value_players['value_season'] > 10.0).dropna().reset_index(drop=True)
    
    fpl_gk = fpl_data[fpl_data['position'] == 'Goalkeeper'].reset_index(drop=True)
    fpl_def = fpl_data[fpl_data['position'] == 'Defender'].reset_index(drop=True)
    fpl_mid = fpl_data[fpl_data['position'] == 'Midfielder'].reset_index(drop=True)
    fpl_fwd = fpl_data[fpl_data['position'] == 'Forward'].reset_index(drop=True)

for i in range(0,len(fpl_data)):
    if fpl_data['team'][i] == 'Man Utd':
        fpl_data['team'][i] = 'Manchester United'
    elif fpl_data['team'][i] == 'Man City':
        fpl_data['team'][i] = 'Manchester City'
    elif fpl_data['team'][i] == 'Newcastle':
        fpl_data['team'][i] = 'Newcastle United'
    elif fpl_data['team'][i] == 'Sheffield Utd':
        fpl_data['team'][i] = 'Sheffield United'
    elif fpl_data['team'][i] == 'Spurs':
        fpl_data['team'][i] = 'Tottenham'
    elif fpl_data['team'][i] == 'Wolves':
        fpl_data['team'][i] = 'Wolverhampton Wanderers'
    elif fpl_data['name'][i] == 'Danny Rose':
        fpl_data['team'][i] = 'Newcastle United,Tottenham'
    elif fpl_data['name'][i] == 'Daniel Drinkwater':
        fpl_data['team'][i] = 'Aston Villa,Burnley'
    elif fpl_data['name'][i] == 'Tariq Lamptey':
        fpl_data['team'][i] = 'Brighton,Chelsea'
    elif fpl_data['name'][i] == 'Cenk Tosun':
        fpl_data['team'][i] = 'Crystal Palace,Everton'
    elif fpl_data['name'][i] == 'Ryan Bennett':
        fpl_data['team'][i] = 'Leicester,Wolverhampton Wanderers'
    elif fpl_data['name'][i] == 'Kyle Walker-Peters':
        fpl_data['team'][i] = 'Southampton,Tottenham'
    else:
        continue
    
def sum_ratio(x,y):
    return (fuzz.ratio(x,y)+fuzz.partial_ratio(x,y)+fuzz.token_sort_ratio(x,y)+fuzz.token_set_ratio(x,y))

cols = player_xStats.columns.tolist()
tst = pd.DataFrame(columns = cols)
for i in range(0,len(fpl_data)):
    for j in range(0,len(player_xStats)):
        if (sum_ratio(fpl_data['name'][i],player_xStats['player_name'][j])>=275)&(fpl_data['team'][i] == player_xStats['team_title'][j]):
            player_xStats['fpl_name'] = fpl_data.iloc[i,0]
            player_xStats['ratio_score'] = sum_ratio(fpl_data['name'][i],player_xStats['player_name'][j])
            tst = tst.append(pd.DataFrame(player_xStats.iloc[[j]]),ignore_index = True)
        else:
            continue
ratio_check = tst[['fpl_name','player_name','ratio_score']]
merge_data = tst.drop(index = [185,116,277,104,220,321,228])
initial_merge = fpl_data.merge(merge_data, left_on = 'name', right_on = 'fpl_name', how = 'inner')