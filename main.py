from kivy.app import App

from kivy.lang import Builder
from kivy.config import Config
from kivy.clock import Clock
from kivy.uix.button import Button
from screens import HomeScreen, StatsScreen, StartupScreen, Screen
from kivy.core.window import Window

Window.size = (390, 844)
Config.set('graphics', 'width', '430')
Config.set('graphics', 'height', '932')
Config.set('graphics', 'resizable', '1')

GUI = Builder.load_file('main.kv')

class BilliardsScorekeeping(App):
    def on_start(self):
        Clock.schedule_once(self.switch_to_menu, 2.0)


    def switch_to_menu(self, dt):
        self.root.ids['screen_manager'].transition.duration = 1.0
        self.root.ids['screen_manager'].current = 'home_screen'

    def build(self):
        return GUI

    def change_screen(self, screen_name):
        screen_manager = self.root.ids['screen_manager']
        screen_manager.current = screen_name

if __name__ == '__main__':
    BilliardsScorekeeping().run()