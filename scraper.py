import os
import time
import requests
import json
from functools import lru_cache
from retrying import retry


api_key = os.environ.get('LOL_API_KEY')

base_url = 'https://na.api.pvp.net/api/lol/na/'
urls = dict(summoner_id=base_url + 'v1.4/summoner/by-name/%s?api_key=%s',
            recent_matches=base_url + 'v1.3/game/by-summoner/%d/recent?api_key=%s')

@lru_cache(maxsize=100)
def get_summoner_id(summoner_name):
    summoner_name = summoner_name.lower().replace(' ', '')
    url = urls['summoner_id'] % (summoner_name, api_key)
    
    summoner_info = lol_request(url)
    return summoner_info[summoner_name]['id']

@retry(wait_fixed=10)
def get_recent_games(summoner_id):
    url = urls['recent_matches'] % (summoner_id, api_key)

    recent_game_info = lol_request(url)
    return recent_game_info

@retry(wait_fixed=10)
def lol_request(url):
    request_info = requests.get(url)
    if request_info.status_code != 200:
        raise ValueError('Rate limit exceeded')

    return request_info.json()

def update_game_data(summoner_name):
    f = open('previous_games.json', 'r')
    previous_raw_data = f.read()
    if not previous_raw_data:
        setup_initial_data(get_recent_games(get_summoner_id(summoner_name)))
    else:
        return update_data(json.loads(previous_raw_data))

def setup_initial_data(data):
    game_ids = [game['gameId'] for game in data['games']]

    data['game_ids'] = game_ids

    f = open('previous_games.json', 'w')
    f.write(json.dumps(data, indent=4))

def update_data(data):
    summoner_id = data['summonerId']

    recent_games = get_recent_games(summoner_id)
    game_ids = [game['gameId'] for game in recent_games['games']]
    
    new_games = list(set(game_ids) - set(data['game_ids']))
    for game in new_games:
        g = [new_game for new_game in recent_games['games'] if new_game['gameId'] == game]
        data['games'].append(g[0])

    data['game_ids'] = data['game_ids'] + new_games
    f = open('previous_games.json', 'w')
    f.write(json.dumps(data, indent=4))
    if new_games:
        return new_games
    else:
        return 'No new games added'

if __name__ == '__main__':
    #setup_initial_data(get_recent_games(get_summoner_id('thatSpysASpy')))
    while(True):
        new_games = update_game_data('ThatSpysASpy')
        print('UPDATED')
        print(new_games)
        time.sleep(600)
