from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.app import App


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
        # pos_hint = {'center_x': 0.5, 'top': 0.9}

        # 1. POP the custom arguments out of kwargs
        self.target_label = target_label
        self.player_list = player_list
        self.master_list = master_list
        # 2. Call super().__init__ ONLY with the remaining kwargs
        super().__init__(**kwargs)

        grid = self.ids.player_list_grid
        for name in player_list:
            # Create our custom button
            btn = PlayerButton(text=name, size_hint=(None, None), width=dp(200), height= dp(40))
            btn.pos_hint = {'center_x': 0.5}
            btn.player_name = name
            btn.popup = self  # Give the button a reference to this popup
            grid.add_widget(btn)


    def finalize_selection(self, name):
        if name:
            if name not in self.master_list:
                self.master_list.append(name)
            self.target_label.text = name
        self.dismiss()


#clock widget logic
class ClockWidget(BoxLayout):
    seconds_passed = NumericProperty(0)
    timer_text = StringProperty('00:00')
    is_running = BooleanProperty(False)

    def toggle_timer(self):
        btn = self.ids.play_pause_btn
        if self.is_running:
            #stop the timer
            Clock.unschedule(self.update_timer)
            btn.background_normal = 'images/play.png'
            btn.background_down = 'images/play.png'
        else:
            #start the timer
            Clock.schedule_interval(self.update_timer, 1)
            btn.background_normal = 'images/pause.png'
            btn.background_down = 'images/pause.png'


        self.is_running = not self.is_running

    def update_timer(self, dt):
        self.seconds_passed += 1
        minutes = self.seconds_passed // 60
        seconds = self.seconds_passed % 60
        self.timer_text = f'{minutes:02}:{seconds:02}'



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
        app.player1, app.current_player = self.player_list[0], self.player_list[0]
        app.player2 = self.player_list[1]
        if self.ids.player1_breaks.state == 'down':
            print("Player 1 breaks!")

        elif self.ids.player2_breaks.state == 'down':
            print("Player 2 breaks!")
            app.player1, app.current_player = self.player_list[1], self.player_list[1]
            app.player2 = self.player_list[0]

    def validate_toggle(self, current_btn):
        if self.ids.player1_breaks.state == 'normal' and self.ids.player2_breaks.state == 'normal':
            current_btn.state = 'down'


    def start_game(self):
        if len(self.selected_players) == 2:
            app = App.get_running_app()
            # Store the data in the app so the gameplay screen can access it
            app.player1 = self.selected_players[0]
            app.player2 = self.selected_players[1]

            # Switch to your gameplay screen
            self.manager.current = 'gameplay_screen'
        else:
            print("Please select exactly 2 players!")



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
    #change player and record turn metrics
    def change_player(self):
        app = App.get_running_app()
        if self.ids.safety_toggle.state == 'down':
            print(f"{app.current_player} played a safety this turn!")
            self.ids.safety_toggle.state = 'normal'
            if app.current_player == app.player1:
                app.player1_defense +=1
            else:
                app.player2_defense += 1


        #this code has to run last in method!!!
        if app.current_player == app.player1:
            app.current_player = app.player2
        else:
            app.current_player = app.player1





class MatchScreen9(Screen):
    pass