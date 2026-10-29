from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty, ObjectProperty, DictProperty
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

    def check_both_players_ready(self):
        """Helper to check if both player slots on the SetupScreen have names."""
        app = App.get_running_app()
        setup_screen = app.root.ids.setup_screen

        p1_text = setup_screen.ids.p1_slot.name_label.text.strip()
        p2_text = setup_screen.ids.p2_slot.name_label.text.strip()

        # Explicitly update the boolean property
        setup_screen.players_ready = bool(p1_text and p2_text)
        print(f"Players Ready State: {setup_screen.players_ready}")  #


    def finalize_selection(self, selected_player_obj):
        app = App.get_running_app()
        typed_name = self.ids.new_player_input.text.strip()

        # 1. Check if the app slot is currently None, and initialize a fresh Player object if so
        if self.slot_id == 1:
            if app.player1 is None:
                app.player1 = Player(name="", user_id="")  # Assuming 'Player' is your class from data.py
            target_slot = app.player1
        else:
            if app.player2 is None:
                app.player2 = Player(name="", user_id="")
            target_slot = app.player2

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

        # 2. Force an explicit UI refresh on the setup screen labels so they update instantly
        setup_screen = app.root.ids.setup_screen
        if self.slot_id == 1:
            setup_screen.ids.p1_slot.name_label.text = target_slot.name
        else:
            setup_screen.ids.p2_slot.name_label.text = target_slot.name

        self.check_both_players_ready()
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

    #popup function for game end summary
    def show_popup(self):
        popup = GameEndSummary()
        popup.open()

        # validate toggle function for play again.
    def validate_toggle(self, current_btn):
        if self.ids.yes.state == 'normal' and self.ids.no.state == 'normal':
            current_btn.state = 'down'


    def on_ball_toggle(self, button, state, group_type):
        """Automatically runs whenever any ball button is clicked."""
        if state == 'down':
            if group_type == 'opp_balls':
                self.selected_opp_ball = button.ball_value
                print(f'Oppenent had {self.selected_opp_ball} balls left!')
            elif group_type == 'player_balls':
                self.selected_player_ball = button.ball_value
                print(f'Current player had {self.selected_player_ball} balls left!')

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


    def early_8(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player.name} made 8ball early!"
        if self.player1 == app.current_player:
            self.player2.add_win()
            app.p2_wins += 1
            self.game_winner = app.player2
        else:
            self.game_winner = app.player1
            self.player1.add_win()
            app.p1_wins += 1

        app.record_turn_time()
        app.turns += 1
        app.innings = app.turns // 2
        # this code has to run last in method!!!

        app.current_player = self.player2 if app.current_player == self.player1 else self.player1



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
        # Capture player balls remaining if early 8 is toggled down, otherwise default to 0 (cleared/won) or handle as needed
        p1_balls_rem = self.selected_player_ball if self.ids.early_8.state == 'down' else 0

        buttons = [self.ids.made_8ball, self.ids.early_8, self.ids.wrong_pocket, self.ids.scratched]

        #error label for submitting without a game end choice
        if not any(btn.state == 'down' for btn in buttons):
            # Update the label instead of just printing
            self.ids.error_label.text = "Please select a reason before submitting."
            return  # Stop here so the popup stays open

        if self.selected_opp_ball is None:
            self.ids.error_label.text = "Please select opponent balls remaining!"
            return

        app = App.get_running_app()
        if self.ids.made_8ball.state == 'down':
            self.made_8ball()
        elif self.ids.early_8.state == 'down':
            self.early_8()

        elif self.ids.wrong_pocket.state == 'down':
            self.made_8ball_wrong_pocket()

        elif self.ids.scratched.state == 'down':
            self.scratched_on_8ball()


        # --- PLAYER OBJECT UPDATE LOGIC to record balls remaining history---
        current_shooter = app.current_player
        opponent_player = self.player2 if current_shooter == self.player1 else self.player1

        if p1_balls_rem is not None:
            current_shooter.update_balls_made(p1_balls_rem)

        if p2_balls_rem is not None:
            opponent_player.update_balls_made(p2_balls_rem)


        # 1. Create a structured entry for this match

        #get todays date and time for timestamp
        current_date= datetime.now().strftime("%m-%d-%Y")
        current_time = datetime.now().strftime('%I:%M:%S %p')
        print(current_date)
        print(current_time)

        # <-Added safety check to prevent KeyError if match_id is missing --->
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

        # --- Ensure match header keys are explicitly updated here ---
        match_container["player1_wins"] = app.p1_wins
        match_container["player2_wins"] = app.p2_wins
        match_container["player1_safes"] = app.p1_safe
        match_container["player2_safes"] = app.p2_safe
        match_container["match_in_progress"] = True
        match_container["game_type"] = app.game_type

        # 1. Calculate rack time first using your turn data
        total_rack_seconds = sum(turn.get('turn_time', 0) for turn in app.turn_data)
        minutes, seconds = divmod(total_rack_seconds, 60)
        formatted_rack_time = f"{minutes:02}:{seconds:02}"

        game_entry = {
                 "timestamp": current_time,
                "game": app.match_count,
                'rack_time': formatted_rack_time,
                "total_innings": len(app.turn_data) // 2,
                "match_winner": self.game_winner.name,
                "game_end_event": self.game_end_event,
                "player1" : {
                    'name': app.player1.name,
                    'user_id': app.player1.user_id,
                    'balls_made': app.player1.balls_made
                },
                "player2" : {
                    'name': app.player2.name,
                    'user_id': app.player2.user_id,
                    'balls_made': app.player2.balls_made
                },
                "turns": list(app.turn_data)
                }

        # Append your finished game entry
        match_container['games'].append(game_entry)

        match_container["player1_wins"] = app.p1_wins
        match_container["player2_wins"] = app.p2_wins
        match_container["player1_safes"] = app.p1_safe
        match_container["player2_safes"] = app.p2_safe

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

        #revert remaining balls back to None
        self.selected_opp_ball = None
        self.selected_player_ball = None

        # retrieve play again choice and trigger game end summary if user chooses 'no'
        if self.ids.yes.state == 'down':
            # User wants to play another rack, so keep match_in_progress = True and set game_active = True for the next rack
            app.game_active = True
        else:
            print('Game Over!')
            app.match_in_progress = False
            app.game_active = False
            match_container["match_in_progress"] = False
            app.save_data.save(app.game_data, app.user_data_dir)
            self.show_popup()



    def close_popup(self, dt=None):
        self.dismiss()



class BreakGameEnd(Popup):
    def __init__(self, player1, player2, **kwargs):
        super().__init__(**kwargs)
        self.player1 = player1
        self.player2 = player2
        self.game_end_event = ""
        self.game_winner = None

    def show_popup(self):
        popup = GameEndSummary()
        popup.open()

    # validate toggle function for play again.
    def validate_toggle(self, current_btn):
        if self.ids.yes.state == 'normal' and self.ids.no.state == 'normal':
            current_btn.state = 'down'



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

        # <-Added safety check to prevent KeyError if match_id is missing --->
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
                'user_id': app.player1.user_id,
                'balls_made': app.player1.balls_made
            },
            "player2": {
                'name': app.player2.name,
                'user_id': app.player2.user_id,
                'balls_made': app.player2.balls_made
            },
            "total_innings": len(app.turn_data) // 2,
            "match_winner": self.game_winner.name,
            "game_end_event": self.game_end_event,
            "turns": list(app.turn_data)
        }

        # Append your finished game entry
        match_container['games'].append(game_entry)

        match_container["player1_wins"] = app.p1_wins
        match_container["player2_wins"] = app.p2_wins
        match_container["player1_safes"] = app.p1_safe
        match_container["player2_safes"] = app.p2_safe
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

        #retrieve play again choice and trigger game end summary if user chooses 'no'
        if self.ids.yes.state == 'down':
            # User wants to play another rack, so keep match_in_progress = True and set game_active = True for the next rack
            app.game_active = True
        else:
            print('Game Over!')
            app.match_in_progress = False
            app.game_active = False
            match_container["match_in_progress"] = False
            app.save_data.save(app.game_data, app.user_data_dir)
            self.show_popup()

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

class GameEndSummary(Popup):
    app = App.get_running_app()
    if app != None:
        print(app.innings)
        print(app.player1)
        print(app.player2)

    def close(self):
        self.dismiss()

    def quit_game(self):
        app = App.get_running_app()
        app.reset_game_state()
        self.close()
        app.change_screen('home_screen', 'right')


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
            else:
                app.p2_safe -= 1

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