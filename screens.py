from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty, ObjectProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.app import App
from datetime import datetime
from data import *
import uuid




#define logic for select player list
class PlayerButton(Button):
    player_obj = ObjectProperty(None)

    def on_release(self):
        # We call the method on the parent popup (which is 'root')
        # a simpler way: just define a reference!
        self.popup.finalize_selection(self.player_obj)

#popup logic for add player
class PlayerPopup(Popup):
    def __init__(self, slot_id, player_list, master_list, **kwargs):
        self.slot_id = slot_id
        self.player_list = player_list
        self.master_list = master_list
        super().__init__(**kwargs)

        grid = self.ids.player_list_grid
        for p in player_list:
            # Create our custom button
            btn = PlayerButton(text=p.name, player_obj =p, size_hint=(None, None), width=dp(200), height= dp(40))
            btn.pos_hint = {'center_x': 0.5}
            # btn.player_obj = player
            btn.popup = self  # Give the button a reference to this popup
            grid.add_widget(btn)



    def finalize_selection(self, selected_player_obj):
        app = App.get_running_app()
        # player_to_use = None
        # --- CHANGED: Unified logic for both selecting and editing ---
        typed_name = self.ids.new_player_input.text.strip()
        target_slot = app.player1 if self.slot_id == 1 else app.player2

        if typed_name:
            target_slot.name = typed_name
            target_slot.user_id = str(uuid.uuid4())[:8]

            # Add to master list if not already there
            if not any(p.name == typed_name for p in self.master_list):
                self.master_list.append(target_slot)
        elif selected_player_obj:
            # User clicked an existing player: copy their identity over
            target_slot.name = selected_player_obj.name
            target_slot.user_id = selected_player_obj.user_id

        self.dismiss()


#game end popup logic
class GameEndPopup(Popup):
    def __init__(self, player1, player2, **kwargs):
        super().__init__(**kwargs)
        self.player1 = player1
        self.player2 = player2
        self.game_end_event = ""
        self.game_winner = None
        self.selected_opp_ball = None
        self.selected_player_ball = None

    def on_ball_toggle(self, button, state, group_type):
        """Automatically runs whenever any ball button is clicked."""
        if state == 'down':
            if group_type == 'opp_balls':
                self.selected_opp_ball = button.ball_value
            elif group_type == 'player_balls':
                self.selected_player_ball = button.ball_value

    def made_8ball(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player.name} made 8ball"
        self.game_winner = app.current_player
        if self.player1 == app.current_player:
            self.player1.add_win()
            app.p1_wins +=1
        else:
            self.player2.add_win()
            app.p2_wins +=1

        print(self.game_end_event)

    def made_8ball_wrong_pocket(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player.name} made 8ball wrong pocket"
        if self.player1 == app.current_player:
            self.player2.add_win()
            app.p2_wins +=1
            self.game_winner = app.player2
        else:
            self.game_winner = app.player1
            self.player1.add_win()
            app.p1_wins +=1

        app.record_turn_time()
        app.turns += 1
        app.innings = app.turns // 2
        # this code has to run last in method!!!

        app.current_player = self.player2 if app.current_player == self.player1 else self.player1

    def scratched_on_8ball(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player.name} scratched on 8ball"
        if self.player1 == app.current_player:
            self.player2.add_win()
            app.p2_wins +=1
            self.game_winner = app.player2

        else:
            self.player1.add_win()
            app.p1_wins +=1
            app.current_player = app.player2
            self.game_winner = app.player1

        app.record_turn_time()
        app.turns += 1
        app.innings = app.turns // 2
        # this code has to run last in method!!!
        app.current_player = self.player2 if app.current_player == self.player1 else self.player1

    def get_game_results(self):
        p2_balls_rem = self.selected_opp_ball
        p1_balls_rem = self.selected_player_ball if self.ids.early_8.state == 'down' else None

        buttons = [self.ids.made_8ball, self.ids.wrong_pocket, self.ids.scratched]

        if not any(btn.state == 'down' for btn in buttons):
            # Update the label instead of just printing
            self.ids.error_label.text = "Please select a reason before submitting."
            return  # Stop here so the popup stays open

        app = App.get_running_app()
        if self.ids.made_8ball.state == 'down':
            self.made_8ball()

        elif self.ids.wrong_pocket.state == 'down':
            self.made_8ball_wrong_pocket()

        elif self.ids.scratched.state == 'down':
            self.scratched_on_8ball()



        # 1. Create a structured entry for this match

        #get todays date and time for timestamp
        current_date= datetime.now().strftime("%m-%d-%Y")
        current_time = datetime.now().strftime('%I:%M:%S %p')
        print(current_date)
        print(current_time)

        if current_date not in app.game_data or not isinstance(app.game_data[current_date], dict):
            app.game_data[current_date] = {}

        # <--- Initialize the match container using match_id if it doesn't exist yet --->
        if app.match_id not in app.game_data[current_date]:
            app.game_data[current_date][app.match_id] = {
                "match_id": app.match_id,
                "match_ended": False,  # Will flip to True when finished/submitted
                "game_type": app.game_type,
                "games": []
            }

        # 1. Calculate rack time first using your turn data
        total_rack_seconds = sum(turn.get('turn_time', 0) for turn in app.turn_data)
        minutes, seconds = divmod(total_rack_seconds, 60)
        formatted_rack_time = f"{minutes:02}:{seconds:02}"

        game_entry = {
                 "timestamp": current_time,
                "game": app.match_count,
                'rack_time': formatted_rack_time,
                "player1" : {
                    'name': app.player1.name,
                    'user_id': app.player1.user_id
                },
                "player2" : {
                    'name': app.player2.name,
                    'user_id': app.player2.user_id,
                },
                "total_innings": len(app.turn_data)// 2,
                "match_winner": self.game_winner.name,
                "game_end_event": self.game_end_event,
                "turns": list(app.turn_data)
                }


        # 4. Append to the specific list for today
        app.game_data[current_date][app.match_id]['games'].append(game_entry)

        # Set to True if this submission completes your match, or keep False if multi-game continues.
        app.game_data[current_date][app.match_id]["match_ended"] = True


        #save match data to game_data dictionary on disk
        # 5. Notify Kivy that the property has changed
        app.game_data = app.game_data

        # 6. Save using the new method signature (with user_data_dir)
        try:
            app.save_data.save(app.game_data, app.user_data_dir)

            self.ids.error_label.text = "Match saved successfully!"
            self.ids.error_label.color = (0, 1, 0, 1)
            app.match_count += 1
            app.turn_data = []
            app.rack_turn_count = 0
            print(f'Now starting match {app.match_count}')

            # Close after success
            Clock.schedule_once(self.close_popup, 1.5)
            app.start_timer()
        except:
            self.ids.error_label.text = "Match saved failed!"
            self.ids.error_label.color = (1, 0, 0, 1)  # Red

    def close_popup(self, dt=None):
        self.dismiss()



class BreakGameEnd(Popup):
    def __init__(self, player1, player2, **kwargs):
        super().__init__(**kwargs)
        self.player1 = player1
        self.player2 = player2
        self.game_end_event = ""
        self.game_winner = None



    def eight_ball_break(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player.name} made the 8 on the break!"
        self.game_winner = app.current_player
        if self.player1 == app.current_player:
            self.player1.add_win()
            app.p1_wins +=1
        else:
            self.player2.add_win()
            app.p2_wins +=1
        print(self.game_end_event)

    def break_and_run(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player.name} broke and ran!"
        self.game_winner = app.current_player
        if self.player1 == app.current_player:
            self.player1.add_win()
            app.p1_wins +=1
        else:
            self.player2.add_win()
            app.p2_wins +=1
        print(self.game_end_event)


    def made_8_and_scratched(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player.name} made 8 ball but scratched!"
        if self.player1 == app.current_player:
            self.player2.add_win()
            app.p2_wins +=1
            self.game_winner = app.player2

        else:
            self.player1.add_win()
            app.p1_wins +=1
            app.current_player = app.player2
            self.game_winner = app.player1

        app.record_turn_time()
        app.turns += 1
        app.innings = app.turns // 2
        # this code has to run last in method!!!
        app.current_player = self.player2 if app.current_player == self.player1 else self.player1



    def get_game_results(self):
        buttons = [self.ids.eight_ball_break, self.ids.break_and_run, self.ids.scratched]
        if not any(btn.state == 'down' for btn in buttons):
            # Update the label instead of just printing
            self.ids.error_label.text = "Please select a reason before submitting."
            return  # Stop here so the popup stays open

        app = App.get_running_app()
        if self.ids.eight_ball_break.state == 'down':
            self.eight_ball_break()

        elif self.ids.break_and_run.state == 'down':
            self.break_and_run()

        elif self.ids.scratched.state == 'down':
            self.made_8_and_scratched()

        # 1. Create a structured entry for this match

        # get todays date and time for timestamp
        current_date = datetime.now().strftime("%m-%d-%Y")
        current_time = datetime.now().strftime('%I:%M:%S %p')
        print(current_date)
        print(current_time)

        if current_date not in app.game_data or not isinstance(app.game_data[current_date], dict):
            app.game_data[current_date] = {}

        # <--- Initialize the match container using match_id if it doesn't exist yet --->
        if app.match_id not in app.game_data[current_date]:
            app.game_data[current_date][app.match_id] = {
                "match_id": app.match_id,
                "match_ended": False,  # Will flip to True when finished/submitted
                "game_type": app.game_type,
                "games": []
            }

        # 1. Calculate rack time first using your turn data
        total_rack_seconds = sum(turn.get('turn_time', 0) for turn in app.turn_data)
        minutes, seconds = divmod(total_rack_seconds, 60)
        formatted_rack_time = f"{minutes:02}:{seconds:02}"

        game_entry = {
            "timestamp": current_time,
            "game": app.match_count,
            'rack_time': formatted_rack_time,
            "player1": {
                'name': app.player1.name,
                'user_id': app.player1.user_id
            },
            "player2": {
                'name': app.player2.name,
                'user_id': app.player2.user_id,
            },
            "total_innings": len(app.turn_data) // 2,
            "match_winner": self.game_winner.name,
            "game_end_event": self.game_end_event,
            "turns": list(app.turn_data)
        }

        # 4. Append to the specific list for today
        app.game_data[current_date][app.match_id]['games'].append(game_entry)

        # Set to True if this submission completes your match, or keep False if multi-game continues.
        app.game_data[current_date][app.match_id]["match_ended"] = True

        # save match data to game_data dictionary on disk
        # 5. Notify Kivy that the property has changed
        app.game_data = app.game_data

        # 6. Save using the new method signature (with user_data_dir)
        try:
            app.save_data.save(app.game_data, app.user_data_dir)

            self.ids.error_label.text = "Match saved successfully!"
            self.ids.error_label.color = (0, 1, 0, 1)
            app.match_count += 1
            app.turn_data = []
            app.rack_turn_count = 0
            print(f'Now starting match {app.match_count}')

            # Close after success
            Clock.schedule_once(self.close_popup, 1.5)
            app.start_timer()
        except:
            self.ids.error_label.text = "Match saved failed!"
            self.ids.error_label.color = (1, 0, 0, 1)  # Red

    def close_popup(self, dt=None):
        self.dismiss()


class ExitGamePopup(Popup):
    def close(self):
        self.dismiss()

    def quit_game(self):
        app = App.get_running_app()
        app.reset_game_state()
        self.close()
        app.change_screen('home_screen', 'right')


#clock widget logic
class ClockWidget(BoxLayout):
    def toggle_timer(self):
        app = App.get_running_app()
        app.toggle_timer()

        btn = self.ids.play_pause_btn
        btn.background_normal = 'images/pause.png' if app.is_running else 'images/play.png'


class SetupScreen(Screen):
    player_list = ListProperty([])


    def show_popup(self, slot_id):
        app = App.get_running_app()

        # --- CHANGED: Check name strings on app.player1 and app.player2 directly instead of UI labels ---
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
        app.match_id = str(uuid.uuid4())[:8]
        print(f'Rack turn count: {app.rack_turn_count}')

        # Check if the player name labels inside the slots are empty
        p1_name = self.ids.p1_slot.name_label.text.strip()
        p2_name = self.ids.p2_slot.name_label.text.strip()

        if not p1_name or not p2_name:
            self.ids.setup_error_label.text = "Please add players to start match!"
            return

        self.ids.setup_error_label.text = ""
        self.won_break(app)

        # Save players right before starting the match
        SaveData.save_players(self.player_list, app.user_data_dir)
        app.players = self.player_list
        # Then change to your match screen
        app.change_screen('match_screen8')
        app.start_timer()
        app.match_started = True


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
        # --- CHANGED: Switch current_player object reference directly ---
        app.current_player = app.player2 if app.current_player == app.player1 else app.player1
        if app.played_safe == True:
            app.played_safe = False

    def previous_player(self):
        app = App.get_running_app()
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
            # 1. Revert lifetime object attribute
            turn_player.total_safeties -= 1

            # 2. Revert the temporary UI app variable displayed on screen
            if turn_player == app.player1:
                app.p1_safe -= 1
            else:
                app.p2_safe -= 1

        # --- Revert current_player object reference directly ---
        app.current_player = app.player2 if app.current_player == app.player1 else app.player1

        #remove the last entry in the turn data list, updates when next player button is pressed
        app.turn_data.pop()



class MatchScreen9(Screen):
    pass