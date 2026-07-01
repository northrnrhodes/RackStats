from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ListProperty
from kivy.metrics import dp
from kivy.app import App



class PlayerButton(Button):
    player_name = StringProperty("")

    def on_release(self):
        # We call the method on the parent popup (which is 'root')
        # a simpler way: just define a reference!
        self.popup.finalize_selection(self.player_name)


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

class GameSetupScreen(Screen):
    pass


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
    pass

class MatchScreen9(Screen):
    pass