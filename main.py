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
from kivy.utils import platform
from kivy.app import App

#platform check for watchdog (live preview editing for kivy)
# 3. Watchdog Desktop-Only Block (Right here, before your App class)
if platform not in ('ios', 'android'):
    # open kivy window on external screen so it doesnt warped widgets
    from kivy.config import Config

    # Force Kivy to use custom coordinates and override any saved cache
    Config.set('graphics', 'position', 'custom')
    Config.set('graphics', 'right', '2000')  # Your external monitor X coordinate
    Config.set('graphics', 'top', '100')
    Config.write()  # Writes this to ensure it overrides cache on restart

    Window.size = (430, 932)

    try:
        import sys
        import os
        from kivy.lang import Builder
        from kivy.clock import Clock
        from kivy.app import App
        from watchdog.observers.polling import \
            PollingObserver as Observer  # Uses bulletproof polling instead of OS hooks
        from watchdog.events import FileSystemEventHandler


        class LocalDevHandler(FileSystemEventHandler):
            def on_any_event(self, event):
                if event.is_directory:
                    return

                target_path = getattr(event, 'dest_path', None) or event.src_path

                # 1. Python file changes still restart the application process
                if target_path.endswith('.py'):
                    print(f"\n🔥 [Watchdog] Python code change detected: {target_path}")
                    print("🔄 Restarting app with latest changes...")
                    os.execv(sys.executable, [sys.executable] + sys.argv)

                # 2. KV file changes hot-reload LIVE without closing the window!
                elif target_path.endswith('.kv'):
                    print(f"\n✨ [Watchdog] KV layout change detected: {target_path}")
                    Clock.schedule_once(lambda dt: self.hot_reload_kv(target_path), 0)

            def hot_reload_kv(self, filepath):
                try:
                    print(f"🔄 Hot-reloading KV file in-place...")

                    # 1. Grab the app instance and find the active ScreenManager to remember your spot
                    app = App.get_running_app()
                    current_screen_name = None

                    if app and app.root:
                        sm = self._find_screen_manager(app.root)
                        if sm:
                            current_screen_name = sm.current
                            print(f"📍 Saving current screen state: '{current_screen_name}'")

                    # 2. Unload and reload the updated KV file
                    Builder.unload_file(filepath)
                    Builder.load_file(filepath)

                    # 3. Rebuild the root UI tree inside the active window
                    if app and hasattr(app, 'root') and app.root:
                        parent = app.root.parent
                        if parent:
                            parent.remove_widget(app.root)
                        app.root = app.build() if hasattr(app, 'build') else None
                        if app.root and parent:
                            parent.add_widget(app.root)

                    # 4. Restore you right back to the screen you were editing!
                    if current_screen_name and app and app.root:
                        new_sm = self._find_screen_manager(app.root)
                        if new_sm:
                            try:
                                # Temporarily kill transition duration so it snaps instantly
                                original_transition = new_sm.transition
                                original_duration = getattr(original_transition, 'duration', 0)
                                original_transition.duration = 0

                                new_sm.current = current_screen_name

                                # Restore the original transition animation for normal app use
                                original_transition.duration = original_duration

                                print(f"📍 Restored screen instantly to: '{current_screen_name}'")
                            except Exception as e:
                                print(f"⚠️ Could not restore screen state: {e}")

                except Exception as e:
                    print(f"❌ Failed to hot-reload KV: {e}")

            def _find_screen_manager(self, widget):
                # Helper to recursively search for a ScreenManager anywhere in your widget tree
                from kivy.uix.screenmanager import ScreenManager
                if isinstance(widget, ScreenManager):
                    return widget
                for child in widget.children:
                    sm = self._find_screen_manager(child)
                    if sm:
                        return sm
                return None


        event_handler = LocalDevHandler()
        observer = Observer()

        # Explicitly target the folder where this script is located
        project_dir = os.path.dirname(os.path.abspath(__file__))
        observer.schedule(event_handler, path=project_dir, recursive=True)
        observer.start()
        print("✅ SUCCESS: Live KV Hot-Reload Watchdog is running and monitoring your project folder!")

    except Exception as e:
        import traceback

        print(f"❌ WATCHDOG FAILED: {e}")
        traceback.print_exc()


4
# # smooths out screen transition
# Window.clearcolor = (16/255, 42/255, 68/255, 1)
#
# # smooths out screen transition to match charcoal background
# Window.clearcolor = (37/255, 37/255, 37/255, 1)

Window.clearcolor = (18/255, 23/255, 24/255, 1)


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

    # #color themes
    # main_color = StringProperty('#102A44') #darkblue
    # accent_color = StringProperty('#A48B5D') #gold

    main_color = StringProperty('#121718') #charcoal grey main canvas
    charcoal_2 = StringProperty('#1A2123')#button/card fills
    # grey_green = StringProperty('#3A5A48') #secondary grey/green
    text_color1 = StringProperty('#4CEB63') #mint green for text
    text_color2 = StringProperty('#FF9F43') #amber/neon orange for text and border highlights
    # accent_color = StringProperty('#FFB259') #bright orange

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
        print(self.player1.wins)
        print(self.player1.safeties)
        print(self.player2.wins)
        print(self.player2.safeties)

        if self.player1:
            self.p1_wins = 0
            self.p1_safeties = 0
            self.player1.wins = 0
            self.player1.safeties = 0

        if self.player2:
            self.p2_wins = 0
            self.p2_safeties = 0
            self.player2.wins = 0
            self.player2.safeties = 0

        print(self.player1.wins)
        print(self.player1.safeties)
        print(self.player2.wins)
        print(self.player2.safeties)



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