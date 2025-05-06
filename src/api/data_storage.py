import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Any
import logging
import csv

class DataStorage:
    def __init__(self, base_dir: str = "data"):
        """Initialize data storage with base directory for data files"""
        self.base_dir = base_dir
        self.json_dir = os.path.join(base_dir, "json")
        self.db_path = os.path.join(base_dir, "fantasy_football.db")
        
        # Create directories if they don't exist
        os.makedirs(self.json_dir, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create players table with additional fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                player_id TEXT PRIMARY KEY,
                name TEXT,
                team TEXT,
                position TEXT,
                status TEXT,
                uniform_number TEXT,
                percent_owned REAL,
                ownership_trend INTEGER,
                timestamp DATETIME,
                season INTEGER,
                bye_week INTEGER,
                is_undroppable BOOLEAN
            )
        ''')
        
        # Create player_stats table with detailed statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_stats (
                player_id TEXT,
                stat_category TEXT,
                stat_value REAL,
                week INTEGER,
                season INTEGER,
                timestamp DATETIME,
                FOREIGN KEY(player_id) REFERENCES players(player_id)
            )
        ''')
        
        # Create draft_analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS draft_analysis (
                player_id TEXT,
                average_pick REAL,
                percent_drafted REAL,
                average_round REAL,
                average_cost REAL,
                timestamp DATETIME,
                season INTEGER,
                FOREIGN KEY(player_id) REFERENCES players(player_id)
            )
        ''')
        
        # Create player_ranks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_ranks (
                player_id TEXT,
                rank_type TEXT,
                rank_value INTEGER,
                timestamp DATETIME,
                season INTEGER,
                FOREIGN KEY(player_id) REFERENCES players(player_id)
            )
        ''')
        
        # Create historical_stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_stats (
                player_id TEXT,
                stat_category TEXT,
                stat_value REAL,
                season INTEGER,
                week INTEGER,
                game_date DATE,
                opponent TEXT,
                FOREIGN KEY(player_id) REFERENCES players(player_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_players_json(self, players_data: Dict[str, Any], season: int):
        """Save players data to JSON file with timestamp"""
        timestamp = datetime.now().isoformat()
        filename = f"players_{season}_{timestamp}.json"
        filepath = os.path.join(self.json_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'season': season,
                'data': players_data
            }, f, indent=2)
        
        return filepath
    
    def save_players_db(self, players_data: Dict[str, Any], season: int):
        """Save players data to SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now()
        
        try:
            for player_id, player_info in players_data.items():
                # Handle nested player data structure
                if isinstance(player_info, dict) and 'player' in player_info:
                    player = player_info['player'][0]
                    
                    # Extract basic player info
                    name = player.get('name', '')
                    team = player.get('editorial_team_full_name', '')
                    position = player.get('display_position', '')
                    status = player.get('status', '')
                    uniform_number = player.get('uniform_number', '')
                    
                    # Insert player record
                    cursor.execute('''
                        INSERT OR REPLACE INTO players 
                        (player_id, name, team, position, status, uniform_number,
                        timestamp, season)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (player_id, name, team, position, status, uniform_number,
                          timestamp, season))
                    
                    # Insert player stats if available
                    if 'stats' in player and player['stats']:
                        for stat_id, stat_value in player['stats'].items():
                            cursor.execute('''
                                INSERT INTO player_stats 
                                (player_id, stat_category, stat_value, season,
                                timestamp)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (player_id, str(stat_id), str(stat_value), season,
                                 timestamp))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            logging.error(f"Error saving to database: {str(e)}")
            raise
        
        finally:
            conn.close()
    
    def get_players(self, season: int = None) -> List[Dict]:
        """Retrieve players from database with extended information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT p.player_id, p.name, p.team, p.position, p.status,
                   p.uniform_number, p.percent_owned, p.ownership_trend,
                   p.timestamp, p.bye_week, p.is_undroppable
            FROM players p
        '''
        params = []
        
        if season:
            query += ' WHERE p.season = ?'
            params.append(season)
        
        cursor.execute(query, params)
        players = []
        
        for row in cursor.fetchall():
            player = {
                'player_id': row[0],
                'name': row[1],
                'team': row[2],
                'position': row[3],
                'status': row[4],
                'uniform_number': row[5],
                'percent_owned': row[6],
                'ownership_trend': row[7],
                'timestamp': row[8],
                'bye_week': row[9],
                'is_undroppable': row[10]
            }
            
            # Get player stats
            cursor.execute('''
                SELECT stat_category, stat_value, week
                FROM player_stats
                WHERE player_id = ? AND season = ?
            ''', (player['player_id'], season))
            stats = {}
            for stat in cursor.fetchall():
                stats[stat[0]] = {'value': stat[1], 'week': stat[2]}
            player['stats'] = stats
            
            # Get draft analysis
            cursor.execute('''
                SELECT average_pick, percent_drafted, average_round, average_cost
                FROM draft_analysis
                WHERE player_id = ? AND season = ?
            ''', (player['player_id'], season))
            draft = cursor.fetchone()
            if draft:
                player['draft_analysis'] = {
                    'average_pick': draft[0],
                    'percent_drafted': draft[1],
                    'average_round': draft[2],
                    'average_cost': draft[3]
                }
            
            # Get player ranks
            cursor.execute('''
                SELECT rank_type, rank_value
                FROM player_ranks
                WHERE player_id = ? AND season = ?
            ''', (player['player_id'], season))
            ranks = {rank[0]: rank[1] for rank in cursor.fetchall()}
            player['ranks'] = ranks
            
            players.append(player)
        
        conn.close()
        return players
    
    def export_to_csv(self, season: int = None, output_path: str = None) -> str:
        """Export player data to CSV file"""
        if output_path is None:
            os.makedirs('data/exports', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'data/exports/players_{season}_{timestamp}.csv'
            
        players = self.get_players(season)
        
        # Define CSV headers based on our data structure
        headers = [
            'player_id', 'name', 'team', 'position', 'status',
            'uniform_number', 'percent_owned', 'ownership_trend',
            'timestamp', 'bye_week', 'is_undroppable'
        ]
        
        # Add stats headers if we have any
        if players and players[0].get('stats'):
            stat_headers = [f'stat_{k}' for k in players[0]['stats'].keys()]
            headers.extend(stat_headers)
            
        # Add ranks headers if we have any
        if players and players[0].get('ranks'):
            rank_headers = [f'rank_{k}' for k in players[0]['ranks'].keys()]
            headers.extend(rank_headers)
        
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for player in players:
                row = {k: player.get(k) for k in headers if k in player}
                
                # Add stats to row
                if 'stats' in player:
                    for stat_id, stat_info in player['stats'].items():
                        if isinstance(stat_info, dict):
                            row[f'stat_{stat_id}'] = stat_info.get('value')
                        else:
                            row[f'stat_{stat_id}'] = stat_info
                
                # Add ranks to row
                if 'ranks' in player:
                    for rank_type, rank_value in player['ranks'].items():
                        row[f'rank_{rank_type}'] = rank_value
                
                writer.writerow(row)
        
        return output_path