from kivy.core.window import Window
from kivy.utils import platform
from kivy.app import App


def platform_check_config():
    #platform check for watchdog (live preview editing for kivy)
    # 3. Watchdog Desktop-Only Block (Right here, before your App class)
    if platform not in ('ios', 'android'):
        print('Platform is not ios or android')
        # open kivy window on external screen so it doesnt warped widgets
        from kivy.config import Config

        # Force Kivy to use custom coordinates and override any saved cache
        Config.set('graphics', 'position', 'custom')
        Config.set('graphics', 'right', '2000')  # Your external monitor X coordinate
        Config.set('graphics', 'top', '100')
        Config.write()  # Writes this to ensure it overrides cache on restart

        Window.size = (430, 932)
        Window.minimum_width = 375
        Window.minimum_height = 650

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
