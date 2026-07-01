from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
import screens
from kivy.core.window import Window
from kivy.properties import ListProperty, StringProperty, NumericProperty, BooleanProperty


#comment out this code before building in xcode
Window.size = (430, 932)

# smooths out screen transition
Window.clearcolor = (16/255, 42/255, 68/255, 1)

class BilliardsScorekeeping(App):
    #global app variables
    game_type = StringProperty('')
    players = ListProperty([])
    score = NumericProperty(0)
    player1 = StringProperty('')
    player2 = StringProperty('')

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
        print(self.score)



if __name__ == '__main__':
    BilliardsScorekeeping().run()