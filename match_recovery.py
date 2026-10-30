from kivy.app import App
from datetime import datetime
from kivy.uix.popup import Popup
from kivy.properties import DictProperty, ObjectProperty, NumericProperty, BooleanProperty, ListProperty, StringProperty



#popup logic for resume match modal
class ResumeMatch(Popup):
    unfinished_match = DictProperty({})

    def __init__(self, unfinished_match, **kwargs):
        super().__init__(**kwargs)
        self.unfinished_match = unfinished_match

    def resume_match(self):
        '''Unpacks all app variables, restores state, and navigates to the match screen'''
        app = App.get_running_app()

        # 1. Unpack basic match metadata
        app.match_id = self.unfinished_match.get("match_id", "")
        app.game_type = self.unfinished_match.get("game_type", "")
        app.match_in_progress = True
        app.match_started = True
        app.game_active = True  # Rack was active when interrupted

        # 2. Restore match clock (match_seconds)
        app.match_seconds = self.unfinished_match.get("match_seconds", 0)
        mm, ss = divmod(app.match_seconds, 60)
        app.match_time = f"{mm:02}:{ss:02}"

        # 3. Restore the latest active rack & turns
        games_list = self.unfinished_match.get("games", [])



        # --- Read wins and safes using descriptive keys into p1/p2 app variables ---
        # Use whichever is higher: the header saved count or the dynamic count
        app.p1_wins = self.unfinished_match.get("player1_wins", 0)
        app.p2_wins = self.unfinished_match.get("player2_wins", 0)
        app.p1_safe = self.unfinished_match.get("player1_safes", 0)
        app.p2_safe = self.unfinished_match.get("player2_safes", 0)

        # If you stored an active_rack or need to pull from the last state:
        if "active_rack" in self.unfinished_match:
            active_rack = self.unfinished_match["active_rack"]
            app.turn_data = list(active_rack.get("turns", []))
        else:
            # Fallback if recovering from standard structure
            app.turn_data = []

        total_seconds = 0

        # --- Add up time spent on turns in the current unfinished rack ---
        active_rack_seconds = sum(turn.get("turn_time", 0) for turn in app.turn_data)
        total_seconds += active_rack_seconds


        for game in games_list:
            rack_time_str = game.get("rack_time", "00:00")
            parts = rack_time_str.split(":")
            if len(parts) == 2:
                total_seconds += int(parts[0]) * 60 + int(parts[1])

        if "match_seconds" in self.unfinished_match:
            total_seconds = max(total_seconds, self.unfinished_match.get("match_seconds", 0))

        app.match_seconds = total_seconds
        mm, ss = divmod(app.match_seconds, 60)
        app.match_time = f"{mm:02}:{ss:02}"

        if games_list:
            latest_game = games_list[-1]
            p1_data = latest_game.get("player1", {})
            p2_data = latest_game.get("player2", {})

            app.player1.name = p1_data.get('name', 'Player 1')
            app.player1.user_id = p1_data.get('user_id', '')
            app.player1.balls_made = p1_data.get('balls_made', 0)

            app.player2.name = p2_data.get('name', 'Player 2')
            app.player2.user_id = p2_data.get('user_id', '')
            app.player2.balls_made = p2_data.get('balls_made', 0)

            app.match_count = len(games_list) + 1

            # --- Determine who shoots next based on the last rack winner ---
            # (In standard 8-ball, the loser of the previous rack breaks/shoots first in the next rack)
            winner_name = latest_game.get("match_winner", "")
            if winner_name == app.player1.name:
                app.current_player = app.player2
            else:
                app.current_player = app.player1
            # ------------------------------------------------------------------------
        else:
            app.match_count = 1
            app.current_player = app.player1  # Default to player 1 for fresh matches



        # --- RESTORE CURRENT TURN TIMER and match timers(Seconds passed on current turn) ---
        if app.turn_data:
            last_turn = app.turn_data[-1]
            app.seconds_passed = last_turn.get("turn_time", 0)
            mm, ss = divmod(app.seconds_passed, 60)
            app.timer_text = f"{mm:02}:{ss:02}"
        else:
            app.seconds_passed = 0
            app.timer_text = "00:00"

        # --- Accurately determine current player based on the last recorded turn ---
        if app.turn_data:
            last_turn_player_name = app.turn_data[-1].get("player", "")
            if last_turn_player_name == app.player1.name:
                app.current_player = app.player2
            else:
                app.current_player = app.player1
        else:
            # If no turns taken in this rack yet, fallback to rack rules (loser breaks/shoots first)
            if games_list:
                winner_name = games_list[-1].get("match_winner", "")
                app.current_player = app.player2 if winner_name == app.player1.name else app.player1
            else:
                app.current_player = app.player1

        completed_innings = sum(game.get("total_innings", 0) for game in games_list)
        active_rack_innings = len(app.turn_data) // 2

        app.innings = completed_innings + active_rack_innings
        app.turns = app.innings * 2
        app.rack_turn_count = len(app.turn_data)

        print(f"Resumed match {app.match_id} | Current Shooter: {app.current_player.name} | Time: {app.match_time}")

        # 4. Navigate to match screen and boot up timer, dismiss popup
        app.change_screen('match_screen8')
        app.start_timer()
        self.dismiss()

    def discard_match(self):
        '''Deletes/discards partial match data and goes to a fresh setup screen'''
        app = App.get_running_app()

        # Mark match as no longer in progress on disk
        current_date = datetime.now().strftime("%m-%d-%Y")
        # ---Grab match_id directly from self.unfinished_match instead of app.match_id ---
        target_match_id = self.unfinished_match.get("match_id", "")
        print(f"Attempting to discard match ID: {target_match_id} for date: {current_date}")

        # Check if the match exists in memory and completely delete it
        if current_date in app.game_data and target_match_id in app.game_data[current_date]:
            del app.game_data[current_date][target_match_id]

            # Optional cleanup: if no matches are left for today, remove the date key too
            if not app.game_data[current_date]:
                del app.game_data[current_date]

            # Force Kivy property notification
            app.game_data = app.game_data

            # Save the updated data dictionary to disk so the deletion is permanent
            try:
                app.save_data.save(app.game_data, app.user_data_dir)
                print(f"Match {target_match_id} completely deleted from match history.")
            except Exception as e:
                print(f"Failed to save after deleting match: {e}")
        else:
            print(f"Warning: Match {target_match_id} under date {current_date} was not found in app.game_data!")

        self.dismiss()

        # Go to clean setup screen and reset app state flags
        app.match_in_progress = False
        app.match_started = False
        app.game_active = False
        app.change_screen('setup_screen')
