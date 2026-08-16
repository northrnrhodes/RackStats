from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from screens import *
from screens import ExitGamePopup
from kivy.core.window import Window
from kivy.properties import ListProperty, StringProperty, NumericProperty, BooleanProperty, ObjectProperty, DictProperty
from data import *
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image


#comment out this code before building in xcode
Window.size = (430, 932)

# smooths out screen transition
Window.clearcolor = (16/255, 42/255, 68/255, 1)


class ImageButton(ButtonBehavior, Image):
    pass

class BilliardsScorekeeping(App):
    #global app variables
    game_type = StringProperty('')

    match_ended = BooleanProperty(False)
    save_data = ObjectProperty(SaveData())
    match_id = StringProperty('')
    match_in_progress = BooleanProperty(False)
    active_match_data = DictProperty({})
    total_rack_seconds = NumericProperty(0)

    #player and game variables
    players = ListProperty([])
    player1 = ObjectProperty(Player())
    player2 = ObjectProperty(Player())
    p1_wins = NumericProperty(0)
    p2_wins = NumericProperty(0)
    p1_safe = NumericProperty(0)
    p2_safe = NumericProperty(0)
    current_player = ObjectProperty(None, allownone=True)

    turns = NumericProperty(0)
    rack_turn_count = NumericProperty(0)
    innings = NumericProperty(0)
    match_count = NumericProperty(1)
    played_safe = BooleanProperty(False)


    #game_clock variables
    match_seconds = NumericProperty(0)
    seconds_passed = NumericProperty(0)
    timer_text = StringProperty('00:00')
    match_time = StringProperty('00:00')
    is_running = BooleanProperty(False)

   #list containing dictionaries with player_object/turn_times key:value pairs
    turn_data = ListProperty([])
    game_data = DictProperty()

    #color themes
    main_color = StringProperty('#102A44') #darkblue
    accent_color = StringProperty('#A48B5D') #gold

    def on_start(self):
        Clock.schedule_once(self.switch_to_menu, 2.0)


    def switch_to_menu(self, dt):
        self.root.ids['screen_manager'].transition.duration = 1.0
        self.root.ids['screen_manager'].current = 'home_screen'

    #builds the UI and loads user data
    def build(self):
        GUI = Builder.load_file('main.kv')
        loaded_data = SaveData.load(self.user_data_dir)

        # 2. Safely update the property
        if isinstance(loaded_data, dict):
            self.game_data.update(loaded_data)
        print(self.game_data)

        # <--- Check match history for any unsubmitted/unfinished match after a crash or exit --->
        unfinished_match = SaveData.get_unfinished_match(self.user_data_dir)

        if unfinished_match:
            self.match_in_progress = True
            self.match_id = unfinished_match.get("match_id", "")
            self.active_match_data = unfinished_match
            self.game_type = unfinished_match.get("game_type", "")
            print(f"Unfinished match detected! Recovering match ID: {self.match_id}")

        # TODO: Add your logic here to unpack `unfinished_match` back into your
        # TODO RAM variables (e.g., racks, innings, players, timers) if you want them restored.
        else:
            self.match_in_progress = False
            print("No unfinished matches found. Starting fresh.")

        # --- LOAD SAVED PLAYERS INTO SETUP SCREEN ---
        # Find the setup screen via screen manager and populate its player_list
        setup_screen = GUI.ids.screen_manager.get_screen('setup_screen')
        loaded_players = SaveData.load_players(self.user_data_dir, Player)
        if loaded_players:
            setup_screen.player_list = loaded_players

        return GUI

    def change_screen(self, screen_name, direction='left'):
        screen_manager = self.root.ids['screen_manager']
        screen_manager.transition.duration = .25
        screen_manager.transition.direction = direction
        screen_manager.current = screen_name
        # screen = self.root.ids.game_setup_screen


    #retrieves game type and passes it to setup screen
    def get_game_type(self, game):
        self.game_type = game
        self.change_screen('setup_screen')
        print(self.game_type)


    #game_clock logic
    def start_timer(self):
        Clock.unschedule(self.update_timer)
        if not self.is_running:
            self.is_running = True
            self.timer_event = Clock.schedule_interval(self.update_timer, 1)


    def stop_timer(self):
        if self.is_running:
            self.is_running = False
            Clock.unschedule(self.timer_event)


    def update_timer(self, dt):
        self.seconds_passed += 1
        minutes = self.seconds_passed // 60
        seconds = self.seconds_passed % 60
        self.timer_text = f'{minutes:02}:{seconds:02}'

        if self.match_started == True:
            self.match_seconds += 1
            mm, ss = divmod(self.match_seconds, 60)
            self.match_time = f"{mm:02}:{ss:02}"



    def menu_button(self):
        popup = ExitGamePopup()
        popup.open()

    def get_game_state(self):
        if self.match_started == True:
            print("There was a current game in progress. Would you like to continue?")
        else:
            self.match_started = False
            self.change_screen('setup_screen')



    def reset_game_state(self):
        # Reset match timing and state flags
        if self.is_running:
            self.stop_timer()
        self.match_seconds = 0
        self.match_time = '00:00'
        self.match_started = False
        self.is_running = False
        self.seconds_passed = 0
        self.timer_text = '00:00'
        self.rack_turn_count = 0
        self.match_id = ''
        self.turns = 0

        # Reset turn data and innings
        self.turn_data = []
        self.innings = 0

        # Reset player stats if they exist
        self.current_player = None
        if self.player1:
            self.player1.wins = 0
            self.player1.safeties = 0
        if self.player2:
            self.player2.wins = 0
            self.player2.safeties = 0



    def record_turn_time(self):
        # --- ADDED: Method to save and reset timer ---
        self.turn_data.append({'player': self.current_player.name, 'turn_time': self.seconds_passed, 'played_safe': self.played_safe})
        if self.played_safe:
            self.played_safe = False
        self.seconds_passed = 0
        self.timer_text = '00:00'

        print(f'Match has started: {self.match_started}')
        for turn in self.turn_data:
            print(turn)




if __name__ == '__main__':
    BilliardsScorekeeping().run()