from kivy.event import EventDispatcher
from kivy.properties import StringProperty, NumericProperty, ListProperty
import json
import os
from kivy.app import App
from datetime import datetime





class Player(EventDispatcher):
    name = StringProperty("")
    user_id = StringProperty(None)
    safeties = NumericProperty(0)
    wins = NumericProperty(0)

    #records balls made per rack, length of list is total games played
    balls_made = NumericProperty(0)


    def play_safety(self):
        self.safeties += 1

    def add_win(self):
        self.wins += 1

    def update_balls_made(self, balls_remaining):
        if balls_remaining is not None:
            self.balls_made += (7 - balls_remaining)



#temporary data saving logic for local disk

class SaveData():
    @staticmethod
    def get_path(user_data_dir):
        '''retrieves directory for match history data. creates directory if it doesn't exist'''

        if 'Documents' in user_data_dir:
            documents_dir = user_data_dir.split('Documents')[0] + 'Documents'
        elif 'Library' in user_data_dir:
            # Splits path to jump from 'Library/...' to the root, then into 'Documents'
            documents_dir = os.path.join(user_data_dir.split('Library')[0], 'Documents')
        else:
            documents_dir = user_data_dir

        return os.path.join(documents_dir, 'match_history.json')

    @staticmethod
    def get_player_path(user_data_dir):
        '''retrieves directory for available users list. creates directory if it doesn't exist'''

        if 'Documents' in user_data_dir:
            documents_dir = user_data_dir.split('Documents')[0] + 'Documents'
        elif 'Library' in user_data_dir:
            documents_dir = os.path.join(user_data_dir.split('Library')[0], 'Documents')

        else:
            documents_dir = user_data_dir

        return os.path.join(documents_dir, 'player_list.json')




    @classmethod
    def save(cls, data, user_data_dir):
        '''saves match history data to directory'''
        try:
            path = cls.get_path(user_data_dir)
            # Safely ensure the directory exists ---
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, 'w') as f:
                json.dump(data, f, indent=4)

            print(f"Match data successfully saved to: {path}")

        except Exception as e:
            print(f'Failed to save: {e}')

    @classmethod
    def load(cls, user_data_dir):
        '''loads all game data into memory'''
        path = cls.get_path(user_data_dir)
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    # Force return empty dict if the file contains something invalid
                    return data if isinstance(data, dict) else {}
            except (json.JSONDecodeError, Exception):
                return {}

        return {}


    @classmethod
    def save_players(cls, players, user_data_dir):
        '''saves player data to directory'''
        try:
            path = cls.get_player_path(user_data_dir)
            os.makedirs(os.path.dirname(path), exist_ok=True)

            player_data = [
                {'name' : p.name, 'user_id': p.user_id}
                for p in players if hasattr(p, 'name')
            ]

            with open(path, 'w') as f:
                json.dump(player_data, f, indent=4)

            print(f"Player data successfully saved to: {path}")
            print("-----------------------------")
            print(json.dumps(player_data, indent=4))
            print("-----------------------------")

        except Exception as e:
            print(f'Failed to save players: {e}')

    @classmethod
    def initialize_new_match(cls, match_id, game_type, user_data_dir):
        history_data = cls.load(user_data_dir)
        today = datetime.now().strftime("%m-%d-%Y")

        if today not in history_data:
            history_data[today] = {}

        history_data[today][match_id] = {
            "match_id": match_id,
            "match_in_progress": True,
            "game_type": game_type,
            "match_seconds": 0,  # <--- Track total match seconds here
            "games": []
        }
        cls.save(history_data, user_data_dir)

    @classmethod
    def auto_save_match(cls, match_id, current_games_list, user_data_dir, match_in_progress=True, current_turns=None):
        '''Updates active match games list, active rack turns, stats, and match status in real time'''
        app = App.get_running_app()
        history_data = cls.load(user_data_dir)

        current_date = datetime.now().strftime("%m-%d-%Y")
        if current_date not in history_data:
            history_data[current_date] = {}

        if match_id not in history_data[current_date]:
            history_data[current_date][match_id] = {
                "match_id": match_id,
                "game_type": getattr(app, 'game_type', '8-Ball'),
                "games": []
            }

        match_container = history_data[current_date][match_id]

        # Update all live metrics directly from app state
        match_container["games"] = current_games_list
        match_container["match_in_progress"] = match_in_progress
        match_container["player1_wins"] = getattr(app, 'p1_wins', 0)
        match_container["player2_wins"] = getattr(app, 'p2_wins', 0)
        match_container["player1_safes"] = getattr(app, 'p1_safe', 0)
        match_container["player2_safes"] = getattr(app, 'p2_safe', 0)

        # Force the exact live turns list into active_rack
        if "active_rack" not in match_container:
            match_container["active_rack"] = {}

        if current_turns is not None:
            match_container["active_rack"]["turns"] = list(current_turns)
        else:
            match_container["active_rack"]["turns"] = list(getattr(app, 'turn_data', []))

        cls.save(history_data, user_data_dir)
        print(f"Disk sync successful! Saved {len(match_container['active_rack']['turns'])} turns to disk.")



    @classmethod
    def get_unfinished_match(cls, user_data_dir):
        '''
                Scans your permanent match history file (grouped by date -> match_id dict)
                for any match entry where match_ended is False, allowing you to resume an unsubmitted match.
                '''
        history_data = cls.load(user_data_dir)

        # history_data is a dictionary where keys are dates and values are dictionaries of matches
        if isinstance(history_data, dict):
            for date_str, matches_dict in history_data.items():
                if isinstance(matches_dict, dict):
                    for match_id, match in matches_dict.items():
                        if isinstance(match, dict) and match.get("match_in_progress") is True:
                            match["match_date"] = date_str  # Attach the date for reference if needed
                            return match

        return None

    @classmethod
    def load_players(cls, user_data_dir, player_class):
        path = cls.get_player_path(user_data_dir)
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    player_data = json.load(f)
                    if isinstance(player_data, list):
                        loaded_players = []
                        for item in player_data:
                            p = player_class(
                                name=item.get("name", ""),
                                user_id=item.get("user_id", "")
                            )
                            loaded_players.append(p)
                        return loaded_players
            except Exception:
                return []

        return []


