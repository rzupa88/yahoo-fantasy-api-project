import requests
from requests_oauthlib import OAuth2Session
import os
from dotenv import load_dotenv
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
from typing import Dict, List, Any
from data_storage import DataStorage

# Load environment variables
load_dotenv()

# Yahoo OAuth2 configuration
CLIENT_ID = os.getenv('YAHOO_CLIENT_ID')
CLIENT_SECRET = os.getenv('YAHOO_CLIENT_SECRET')
# Using a public redirect URL that's registered in Yahoo API console
REDIRECT_URI = 'oob'  # Out-of-band (copy-paste) flow
AUTHORIZATION_BASE_URL = 'https://api.login.yahoo.com/oauth2/request_auth'
TOKEN_URL = 'https://api.login.yahoo.com/oauth2/get_token'

def get_authorization_url():
    """Get the authorization URL for Yahoo login"""
    yahoo = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI)
    authorization_url, state = yahoo.authorization_url(AUTHORIZATION_BASE_URL)
    return authorization_url, state

def get_token_with_code(code):
    """Exchange authorization code for token"""
    yahoo = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI)
    token = yahoo.fetch_token(
        TOKEN_URL,
        client_secret=CLIENT_SECRET,
        code=code
    )
    return token

def test_api_connection(token):
    """Test the API connection by fetching user's games data"""
    base_url = "https://fantasysports.yahooapis.com/fantasy/v2"
    headers = {
        'Authorization': f'Bearer {token["access_token"]}',
        'Content-Type': 'application/json'
    }
    
    # Try to get user's games data
    response = requests.get(
        f"{base_url}/users;use_login=1/games",
        headers=headers,
        params={'format': 'json'}
    )
    
    if response.status_code == 200:
        print("\nAPI Connection Test Successful!")
        print("Games data retrieved:")
        print(json.dumps(response.json(), indent=2))
        return True
    else:
        print(f"\nAPI Connection Test Failed!")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def get_player_stats(base_url: str, game_key: str, player_key: str, headers: Dict) -> Dict:
    """Helper function to get detailed player statistics"""
    response = requests.get(
        f"{base_url}/player/{game_key}.p.{player_key}/stats",
        headers=headers,
        params={'format': 'json'}
    )
    if response.status_code == 200:
        return response.json()
    return {}

def extract_player_info(player_data):
    """Helper function to extract player information from nested data"""
    player_info = {
        'player_id': None,
        'name': None,
        'editorial_team_full_name': None,
        'display_position': None,
        'uniform_number': None,
        'stats': {},
        'metadata': {}
    }
    
    for item in player_data:
        if isinstance(item, dict):
            if 'player_id' in item:
                player_info['player_id'] = item['player_id']
            elif 'name' in item and isinstance(item['name'], dict):
                player_info['name'] = item['name'].get('full')
            elif 'editorial_team_full_name' in item:
                player_info['editorial_team_full_name'] = item['editorial_team_full_name']
            elif 'display_position' in item:
                player_info['display_position'] = item['display_position']
            elif 'uniform_number' in item:
                player_info['uniform_number'] = item['uniform_number']
            elif 'stats' in item and isinstance(item['stats'], list):
                for stat in item['stats']:
                    if isinstance(stat, dict) and 'stat' in stat:
                        stat_info = stat['stat']
                        player_info['stats'][stat_info.get('stat_id')] = stat_info.get('value')
    
    return player_info

def get_nfl_players(token: Dict[str, Any], count: int = 25) -> List[Dict]:
    """
    Fetch NFL player data from Yahoo Fantasy Sports
    """
    base_url = "https://fantasysports.yahooapis.com/fantasy/v2"
    headers = {
        'Authorization': f'Bearer {token["access_token"]}',
        'Content-Type': 'application/json'
    }
    
    # Get current NFL game key
    response = requests.get(
        f"{base_url}/games;is_available=1;game_codes=nfl",
        headers=headers,
        params={'format': 'json'}
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get NFL game data: {response.text}")
    
    games_data = response.json()
    games = games_data['fantasy_content']['games']
    
    # Find the most recent available NFL game
    if games['count'] == 0:
        raise Exception("No active NFL games found. The season might be in offseason.")
        
    game = games['0']['game']
    game_key = game[0]['game_key']
    season = game[0]['season']
    
    print(f"\nFound NFL game for season {season}")
    
    # Get player data using game key
    response = requests.get(
        f"{base_url}/game/{game_key}/players;start=0;count={count}",
        headers=headers,
        params={
            'format': 'json',
            'sort': 'AR',  # Average Rank
            'status': 'A',  # Active players only
            'position': 'O'  # Offense players only
        }
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get player data: {response.text}")
    
    print("\nSuccessfully retrieved player data")
    players_data = response.json()
    
    try:
        if 'fantasy_content' in players_data:
            if 'game' in players_data['fantasy_content']:
                players = {}
                raw_players = players_data['fantasy_content']['game'][1]['players']
                
                # Process each player
                for idx in range(raw_players['count']):
                    player_data = raw_players[str(idx)]['player'][0]
                    player_info = extract_player_info(player_data)
                    
                    if player_info['player_id']:
                        players[player_info['player_id']] = {
                            'player': [player_info]
                        }
                
                # Initialize data storage and save the data
                storage = DataStorage()
                
                # Save to both JSON and SQLite
                json_path = storage.save_players_json(players, int(season))
                print(f"\nSaved player data to JSON: {json_path}")
                
                storage.save_players_db(players, int(season))
                print("\nSaved player data to SQLite database")
                
                return players
            else:
                raise Exception("Unexpected response structure")
    except Exception as e:
        print(f"Response structure: {json.dumps(players_data, indent=2)}")
        raise Exception(f"Error parsing player data: {str(e)}")

if __name__ == "__main__":
    try:
        if not CLIENT_ID or not CLIENT_SECRET:
            raise ValueError("Missing CLIENT_ID or CLIENT_SECRET in .env file")

        print("Starting OAuth flow...")
        print(f"Using Client ID: {CLIENT_ID[:10]}...")

        # Get the authorization URL
        auth_url, state = get_authorization_url()
        print("\nPlease visit this URL to authorize your application:")
        print(auth_url)
        print("\nAfter authorizing, you will receive a verification code.")
        print("Please enter the verification code below:")
        
        # Get the verification code from user input
        verification_code = input("Enter code: ").strip()
        
        # Exchange the verification code for a token
        try:
            token = get_token_with_code(verification_code)
            print("\nAccess token received successfully!")
            
            # Save token to a file
            with open('token.json', 'w') as f:
                json.dump(token, f)
            print("Token saved to token.json")
            
            # Test the API connection
            test_api_connection(token)
            
            # Fetch NFL player data
            print("\nFetching NFL player data...")
            try:
                players = get_nfl_players(token)
                if players:
                    print("\nNFL Players retrieved successfully!")
                    print(f"\nNumber of players retrieved: {len(players)}")
                    
                    # Initialize storage and retrieve the latest data
                    storage = DataStorage()
                    stored_players = storage.get_players(season=2025)  # Current season
                    
                    print(f"\nStored {len(stored_players)} players in the database")
                    print("\nExample player data (first player):")
                    if stored_players:
                        print(json.dumps(stored_players[0], indent=2))
                else:
                    print("\nNo players found in the response")
            except Exception as e:
                print(f"\nError fetching NFL players: {str(e)}")
                if hasattr(e, '__context__') and e.__context__:
                    print(f"Caused by: {str(e.__context__)}")
            
        except Exception as e:
            print(f"\nError exchanging code for token: {e}")
            
    except ValueError as ve:
        print(f"\nConfiguration Error: {ve}")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        import traceback
        print(traceback.format_exc())