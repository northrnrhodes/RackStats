from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.app import App
from datetime import datetime




#define logic for select player list
class PlayerButton(Button):
    player_name = StringProperty("")

    def on_release(self):
        # We call the method on the parent popup (which is 'root')
        # a simpler way: just define a reference!
        self.popup.finalize_selection(self.player_name)

#popup logic for add player
class PlayerPopup(Popup):
    def __init__(self, target_label, player_list, master_list, **kwargs):
        self.target_label = target_label
        self.player_list = player_list
        self.master_list = master_list
        super().__init__(**kwargs)
        # --- CHANGED: Pre-fill input if a name exists (for editing) ---
        if target_label.text != "Select Player":
            self.ids.new_player_input.text = target_label.text

        grid = self.ids.player_list_grid
        for name in player_list:
            # Create our custom button
            btn = PlayerButton(text=name, size_hint=(None, None), width=dp(200), height= dp(40))
            btn.pos_hint = {'center_x': 0.5}
            btn.player_name = name
            btn.popup = self  # Give the button a reference to this popup
            grid.add_widget(btn)



    def finalize_selection(self, new_name):
        # --- CHANGED: Unified logic for both selecting and editing ---
        new_name = new_name.strip()
        old_name = self.target_label.text.strip()

        if new_name:
            if old_name in self.master_list:
                idx = self.master_list.index(old_name)
                self.master_list[idx] = new_name
            elif new_name not in self.master_list:
                self.master_list.append(new_name)

                # 2. Update the label and dismiss
            self.target_label.text = new_name
            self.dismiss()



#game end popup logic
class GameEndPopup(Popup):
    def __init__(self, player1, player2, **kwargs):
        super().__init__(**kwargs)
        self.player1 = player1
        self.player2 = player2
        self.game_end_event = ""
        self.game_winner = None

    def made_8ball(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player} made 8ball"
        self.game_winner = app.current_player
        if self.player1.name == app.current_player:
            self.player1.add_win()
        else:
            self.player2.add_win()

    def made_8ball_wrong_pocket(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player} made 8ball wrong pocket"
        if self.player1.name == app.current_player:
            self.player2.add_win()
            self.game_winner = app.player2.name
        else:
            self.game_winner = app.player1.name
            self.player1.add_win()

        app.record_turn_time()
        app.turns += 1
        app.innings = app.turns // 2
        # this code has to run last in method!!!
        if app.current_player == app.player1.name:
            app.current_player = app.player2.name
        else:
            app.current_player = app.player1.name

    def scratched_on_8ball(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player} scratched on 8ball"
        if self.player1.name == app.current_player:
            self.player2.add_win()
            self.game_winner = app.player2.name

        else:
            self.player1.add_win()
            app.current_player = app.player1.name

        app.record_turn_time()
        app.turns += 1
        app.innings = app.turns // 2
        # this code has to run last in method!!!
        if app.current_player == app.player1.name:
            app.current_player = app.player2.name
        else:
            app.current_player = app.player1.name

    def get_game_results(self):
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

        if current_date not in app.game_data:
            app.game_data[current_date] = []


        match_entry = {
                 "timestamp": current_time,
                "game": app.match_count,
                "player1" : app.player1.name,
                "player2" : app.player2.name,
                "total_innings": len(app.turn_data)// 2,
                "match_winner": self.game_winner,
                "game_end_event": self.game_end_event,
                "turns": list(app.turn_data)
                }


        # 4. Append to the specific list for today
        app.game_data[current_date].append(match_entry)


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
        # 1. Identify which label we are targeting
        p1_label = self.ids.p1_slot.name_label
        p2_label = self.ids.p2_slot.name_label

        if slot_id == 1:
            target = p1_label
            other = p2_label
        else:
            target = p2_label
            other = p1_label

        # 2. Get the name of the player currently in the other slot
        other_name = other.text.strip()

        # 3. Create a filtered list
        filtered_list = []
        for name in self.player_list:
            if name != other_name:
                filtered_list.append(name)

        # 4. Open the popup
        popup = PlayerPopup(
            target_label=target,
            player_list=filtered_list,
            master_list=self.player_list,
        )
        popup.open()


    def won_break(self):
        app = App.get_running_app()
        app.player1.name, app.current_player = self.player_list[0], self.player_list[0]
        app.player2.name = self.player_list[1]

        if self.ids.player1_breaks.state == 'down':
            print(f"{app.player1.name} breaks!")


        elif self.ids.player2_breaks.state == 'down':
            print(f"{app.player2.name} breaks!")
            app.player1.name, app.current_player = self.player_list[1], self.player_list[1]
            app.player2.name = self.player_list[0]


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
        popup = GameEndPopup(
            player1=app.player1,
            player2=app.player2)
        app.is_running = False
        app.stop_timer()
        popup.open()



    #change player and record turn metrics
    def change_player(self):
        app = App.get_running_app()
        app.record_turn_time()
        app.turns += 1
        app.rack_turn_count += 1
        app.innings = app.turns // 2
        if self.ids.safety_toggle.state == 'down':
            print(f"{app.current_player} played a safety this turn!")
            self.ids.safety_toggle.state = 'normal'
            if app.current_player == app.player1.name:
                app.player1.play_safety()
            else:
                app.player2.play_safety()



        #this code has to run last in method!!!
        if app.current_player == app.player1.name:
            app.current_player = app.player2.name
        else:
            app.current_player = app.player1.name

    def previous_player(self):
        app = App.get_running_app()
        app.turns -= 1
        app.rack_turn_count -= 1
        app.innings = app.turns // 2
        app.seconds_passed = app.turn_data[-1]['turn_time']

        # 3. Force the timer text to update
        minutes = app.seconds_passed // 60
        seconds = app.seconds_passed % 60
        app.timer_text = f'{minutes:02}:{seconds:02}'
        app.turn_data.pop()

        # 4. Ensure the timer is running
        # If the user hit 'End Turn' (which stops it), we resume it here
        if not app.is_running:
            app.start_timer()

        #change current player back to other player
        if app.current_player == app.player1.name:
            app.current_player = app.player2.name
        else:
            app.current_player = app.player1.name






class MatchScreen9(Screen):
    pass