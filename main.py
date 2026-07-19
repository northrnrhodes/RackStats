from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from screens import *
from kivy.core.window import Window
from kivy.properties import ListProperty, StringProperty, NumericProperty, BooleanProperty, ObjectProperty, DictProperty
from data import *


#comment out this code before building in xcode
Window.size = (430, 932)

# smooths out screen transition
Window.clearcolor = (16/255, 42/255, 68/255, 1)

class BilliardsScorekeeping(App):
    #global app variables
    game_type = StringProperty('')
    match_started = BooleanProperty(False)
    match_ended = BooleanProperty(False)
    save_data = ObjectProperty(SaveData())

    #player and game variables
    players = ListProperty([])
    player1 = ObjectProperty(Player())
    player2 = ObjectProperty(Player())
    current_player = StringProperty()
    turns = NumericProperty(0)
    rack_turn_count = NumericProperty(0)
    innings = NumericProperty(0)
    match_count = NumericProperty(1)


    #game_clock variables
    seconds_passed = NumericProperty(0)
    timer_text = StringProperty('00:00')
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

    def build(self):
        GUI = Builder.load_file('main.kv')
        loaded_data = SaveData.load(self.user_data_dir)

        # 2. Safely update the property
        if isinstance(loaded_data, dict):
            self.game_data.update(loaded_data)
        return GUI

    def change_screen(self, screen_name, direction='left'):
        screen_manager = self.root.ids['screen_manager']
        screen_manager.transition.duration = .25
        screen_manager.transition.direction = direction
        screen_manager.current = screen_name
        # screen = self.root.ids.game_setup_screen

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

    def record_turn_time(self):
        # --- ADDED: Method to save and reset timer ---
        self.turn_data.append({'player': self.current_player, 'turn_time': self.seconds_passed})
        self.seconds_passed = 0
        self.timer_text = '00:00'

        print(f'Match has started: {self.match_started}')
        for turn in self.turn_data:
            print(turn)





if __name__ == '__main__':
    BilliardsScorekeeping().run()