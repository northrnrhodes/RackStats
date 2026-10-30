from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty
from kivy.metrics import dp
from kivy.uix.button import Button
from data import *
import uuid
from kivy.app import App



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



#popup for quitting match and exiting to main menu
class ExitGamePopup(Popup):
    def close(self):
        self.dismiss()

    def quit_game(self):
        app = App.get_running_app()
        app.reset_game_state()
        self.close()
        app.change_screen('home_screen', 'right')



#shows game end summary popup with match stats
class GameEndSummary(Popup):
    def calculate_shooting_percentage(self, player):
        misses = max(0, player.turns - player.safeties)
        print(misses)
        print(player.turns)
        attempts = misses + player.balls_made
        shooting_percentage = (player.balls_made/ attempts * 100) if attempts > 0 else 0
        return f'{shooting_percentage:.1f}'


    def close(self):
        self.dismiss()

    def quit_game(self):
        app = App.get_running_app()
        app.reset_game_state()
        self.close()
        app.change_screen('home_screen', 'right')
