from kivy.properties import BooleanProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from break_game_end_8 import BreakGameEnd
from game_end_8 import GameEndPopup
from popups import *


#clock widget logic
class ClockWidget(BoxLayout):
    def toggle_timer(self):
        app = App.get_running_app()
        app.toggle_timer()

        btn = self.ids.play_pause_btn
        btn.background_normal = 'images/pause.png' if app.is_running else 'images/play.png'


class SetupScreen(Screen):

    player_list = ListProperty([])
    players_ready = BooleanProperty(False)


    def show_popup(self, slot_id):
        app = App.get_running_app()

        # Check name strings on app.player1 and app.player2 directly instead of UI labels ---
        other_name = app.player2.name if slot_id == 1 else app.player1.name

        filtered_list = [p for p in self.player_list if p.name != other_name]


        # 4. Open the popup
        popup = PlayerPopup(
            slot_id=slot_id,
            player_list=filtered_list,
            master_list=self.player_list,
        )
        popup.open()

    def start_match(self):
        app = App.get_running_app()
        app.match_in_progress = True
        app.game_active = True
        app.match_id = str(uuid.uuid4())[:8]
        print(f'Rack turn count: {app.rack_turn_count}')

        # Check if the player name labels inside the slots are empty
        p1_name = self.ids.p1_slot.name_label.text.strip()
        p2_name = self.ids.p2_slot.name_label.text.strip()

        if not p1_name or not p2_name:
            self.ids.setup_error_label.text = "Please add players to start match!"
            return

        #reset all stats to 0 for new game
        # app.reset_game_state()
        self.ids.setup_error_label.text = ""
        self.won_break(app)

        # Save players right before starting the match
        SaveData.save_players(self.player_list, app.user_data_dir)
        app.players = self.player_list

        # 2. INITIALIZE THE NEW MATCH IN DISK STORAGE (Crucial for crash recovery!)
        SaveData.initialize_new_match(app.match_id, app.game_type, app.user_data_dir)

        # Then change to your match screen
        app.change_screen('match_screen8')
        app.start_timer()



    def won_break(self, app):
        if self.ids.player1_breaks.state == 'down':
            app.current_player = app.player1
            print(f"{app.player1.name} breaks!")


        elif self.ids.player2_breaks.state == 'down':
            app.current_player = app.player2
            print(f"{app.player1.name} breaks!")


    def validate_toggle(self, current_btn):
        if self.ids.player1_breaks.state == 'normal' and self.ids.player2_breaks.state == 'normal':
            current_btn.state = 'down'



class HomeScreen(Screen):
    pass

class StatsScreen(Screen):
    pass

class StartupScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

class ChooseGameScreen(Screen):
    pass

class MatchScreen8(Screen):
    def on_pre_enter(self):
        app = App.get_running_app()
        # Force refresh the player names every time you enter the match screen
        if app.player1:
            self.ids.p1_box.player_name = app.player1.name
        if app.player2:
            self.ids.p2_box.player_name = app.player2.name


    def show_popup(self):
        app = App.get_running_app()
        if app.rack_turn_count == 0:
            popup = BreakGameEnd(
                player1=app.player1,
                player2=app.player2)
        else:
            popup = GameEndPopup(
                player1=app.player1,
                player2=app.player2)
        app.is_running = False
        app.stop_timer()
        popup.open()



    #change player and record turn metrics
    def change_player(self):
        app = App.get_running_app()
        # --- Retrieve current games list & match container safely ---
        current_date = datetime.now().strftime("%m-%d-%Y")

        if current_date not in app.game_data:
            app.game_data[current_date] = {}
        if app.match_id not in app.game_data[current_date]:
            app.game_data[current_date][app.match_id] = {
                "match_id": app.match_id,
                "match_in_progress": True,
                "game_type": app.game_type,
                "games": []
            }

        match_container = app.game_data[current_date][app.match_id]
        games_list = match_container.get("games", [])

        if self.ids.safety_toggle.state == 'down':
            print(f"{app.current_player.name} played a safety this turn!")
            self.ids.safety_toggle.state = 'normal'
            if app.current_player == app.player1:
                app.player1.play_safety()
                app.p1_safe += 1
                app.played_safe = True
            else:
                app.player2.play_safety()
                app.p2_safe += 1
                app.played_safe = True
        app.record_turn_time()
        app.turns += 1
        app.rack_turn_count += 1
        app.innings = app.turns // 2
        app.current_player.turns = +1
        # --- Switch current_player object reference directly ---
        app.current_player = app.player2 if app.current_player == app.player1 else app.player1
        if app.played_safe == True:
            app.played_safe = False

        # --- Save mid-rack turns and stats to 'active_rack' for crash recovery ---
        match_container["player1_wins"] = app.p1_wins
        match_container["player2_wins"] = app.p2_wins
        match_container["player1_safes"] = app.p1_safe
        match_container["player2_safes"] = app.p2_safe


        match_container["active_rack"] = {
            "turns": list(app.turn_data)
        }

        # --- Auto-save state to disk in real-time ---
        SaveData.auto_save_match(
            match_id=app.match_id,
            current_games_list=games_list,
            user_data_dir=app.user_data_dir,
            match_in_progress=True
        )


    def previous_player(self):
        app = App.get_running_app()
        if not app.turn_data:
            print("No turns to undo!")
            return
        #reset previous turn state variables
        app.turns -= 1
        app.rack_turn_count -= 1
        app.innings = app.turns // 2
        app.seconds_passed = app.turn_data[-1]['turn_time']

        # Grab the last turn data before popping it
        last_turn = app.turn_data[-1]

        # 3. Force the timer text to update
        minutes = app.seconds_passed // 60
        seconds = app.seconds_passed % 60
        app.timer_text = f'{minutes:02}:{seconds:02}'
        # 4. Ensure the timer is running
        # If the user hit 'End Turn' (which stops it), we resume it here
        if not app.is_running:
            app.start_timer()

        # --- Revert Safety Data based on WHO took the turn ---
        turn_player = last_turn.get('player')  # The player who made this specific turn

        if last_turn.get('played_safe') == True:
            # 2. Revert the temporary UI app variable displayed on screen
            if turn_player == app.player1.name:
                app.p1_safe -= 1
                app.player1.turns -= 1
            else:
                app.p2_safe -= 1
                app.player2.turns -= 1

        # --- Revert current_player safely using the turn's owner ---
        if turn_player == app.player1.name:
            app.current_player = app.player1
        else:
            app.current_player = app.player2

        #remove the last entry in the turn data list, updates when next player button is pressed
        app.turn_data.pop()

        # ---  Fetch games list, update active rack, and auto-save undo ---
        current_date = datetime.now().strftime("%m-%d-%Y")
        match_container = app.game_data.get(current_date, {}).get(app.match_id, {})
        games_list = match_container.get("games", [])

        if "active_rack" in match_container:
            match_container["active_rack"]["turns"] = list(app.turn_data)

        SaveData.auto_save_match(
            match_id=app.match_id,
            current_games_list=games_list,
            user_data_dir=app.user_data_dir,
            match_in_progress=True
        )



class MatchScreen9(Screen):
    pass