from kivy.event import EventDispatcher
from kivy.properties import StringProperty, NumericProperty
import json
import os
from kivy.app import App




class Player(EventDispatcher):
    name = StringProperty("")
    user_id = StringProperty(None)
    safeties = NumericProperty(0)
    wins = NumericProperty(0)


    def play_safety(self):
        self.safeties += 1


    def add_win(self):
        self.wins += 1



#temporary data saving logic for local disk

class SaveData():
    @staticmethod
    def get_path(user_data_dir):

        if 'Library' in user_data_dir:
            # Splits path to jump from 'Library/...' to the root, then into 'Documents'
            documents_dir = os.path.join(user_data_dir.split('Library')[0], 'Documents')
        else:
            documents_dir = user_data_dir

        return os.path.join(documents_dir, 'match_history.json')

    @classmethod
    def save(cls, data, user_data_dir):
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
