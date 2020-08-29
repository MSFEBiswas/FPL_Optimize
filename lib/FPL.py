#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 21 17:24:46 2020

@author: Ankan Biswas
"""

import requests
import json
import aiohttp
import asyncio
import nest_asyncio
import pandas as pd
import numpy as np
from understat import Understat
from fuzzywuzzy import fuzz

nest_asyncio.apply()

async def all_players():
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        data = await understat.get_league_players("epl", 2019)
        json_ = json.loads((json.dumps(data)))
        return json_

def normalize_to_df(json_string):
    df = pd.json_normalize(json_string).sort_values(by=['player_name']).reset_index(drop=True)
    df = df.drop(['id', 'time', 'position'], axis=1)
    df = df.rename(columns={'team_title': 'team'})
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
    elements_df['player_name'] = elements_df['first_name'] + ' ' + elements_df['second_name']
    
    final_df = elements_df[['id', 'player_name','team', 'position','total_points', 'selected_by_percent', 'now_cost', 'minutes', 'transfers_in', 'value_season']]
    final_df['value_season'] = final_df['value_season'].astype(float)
    final_df = final_df.sort_values(by=['value_season'], ascending=False).reset_index(drop=True)
    final_df['value_minutes'] = (final_df['value_season']/final_df['minutes'])*100
    final_df = final_df.sort_values(by=['player_name']).reset_index(drop=True)
    final_df = final_df.drop(['id'], axis=1)
    return final_df

def team_normalization(data):
    for i in range(len(data)):
        if len(data.iloc[i]['team'].split(',')) > 1:
            data.iloc[i]['team'] = data.iloc[i]['team'].split(',')[0]
    
    for i in range(len(data)):
        if data.iloc[i]['team'] == 'Manchester United':
            data.iloc[i]['team'] = 'Man Utd'
        elif data.iloc[i]['team'] == 'Manchester City':
            data.iloc[i]['team'] = 'Man City'
        elif data.iloc[i]['team'] == 'Newcastle United':
            data.iloc[i]['team'] = 'Newcastle'
        elif data.iloc[i]['team'] == 'Sheffield United':
            data.iloc[i]['team'] = 'Sheffield Utd'
        elif data.iloc[i]['team'] == 'Tottenham':
            data.iloc[i]['team'] = 'Spurs'
        elif data.iloc[i]['team'] == 'Wolverhampton Wanderers':
            data.iloc[i]['team'] = 'Wolves'

def match_score(x,y):
    score = fuzz.ratio(x,y)
    score += fuzz.partial_ratio(x,y)
    score += fuzz.token_sort_ratio(x,y)
    score += fuzz.token_set_ratio(x,y)
    return score

def matching(fpl, stats):
    players_matched = {}
    players_matched['fpl'] = []
    players_matched['understat'] = []
    players_matched['score'] = []
    
    for i in range(len(fpl)):
        filter_df = stats.loc[stats['team'] == fpl.iloc[i]['team']].reset_index(drop=True)
        dummy_dict = {}
        dummy_dict['player'] = [0]
        dummy_dict['ratio'] = [0]
        for j in range(len(filter_df)):
            ratio = match_score(filter_df.iloc[j]['player_name'], fpl.iloc[i]['player_name'])
            if ratio > dummy_dict['ratio'][0]:
                    dummy_dict['player'].pop()
                    dummy_dict['player'].append(filter_df.iloc[j]['player_name'])
                    dummy_dict['ratio'].pop()
                    dummy_dict['ratio'].append(ratio)
        if dummy_dict['ratio'][0] > 260:
            players_matched['fpl'].append(fpl.iloc[i]['player_name'])
            players_matched['understat'].append(dummy_dict['player'][0])
            players_matched['score'].append(dummy_dict['ratio'][0])
    players_matched = pd.DataFrame(players_matched)
    return players_matched

def data_merge(fpl, stats, matched):
    fpl = fpl[fpl.player_name.isin(matched.fpl.tolist())].reset_index(drop=True)
    stats = stats[stats.player_name.isin(matched.understat.tolist())].reset_index(drop=True)
    fpl.player_name = matched.understat
    data = fpl.merge(stats, how='inner', on=['player_name', 'team'])
    return data

def api_init():
    loop = asyncio.get_event_loop()
    json_all_players = loop.run_until_complete(all_players())
    understat = normalize_to_df(json_all_players)
    fpl = connect_fpl_api()
    return fpl, understat

def program_init():
    fpl_data, stats_data = api_init()
    team_normalization(stats_data)
    matched_players = matching(fpl_data, stats_data)
    data = data_merge(fpl_data, stats_data, matched_players)
    return data

if __name__ == "__main__":
    fpl_data, stats_data = api_init()
    all_data = program_init()
