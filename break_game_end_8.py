from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.popup import Popup
from popups import GameEndSummary



class BreakGameEnd(Popup):
    def __init__(self, player1, player2, **kwargs):
        super().__init__(**kwargs)
        self.player1 = player1
        self.player2 = player2
        self.game_end_event = ""
        self.game_winner = None

    def show_popup(self):
        popup = GameEndSummary()
        popup.open()

    # validate toggle function for play again.
    def validate_toggle(self, current_btn):
        if self.ids.yes.state == 'normal' and self.ids.no.state == 'normal':
            current_btn.state = 'down'



    def eight_ball_break(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player.name} made the 8 on the break!"
        self.game_winner = app.current_player
        if self.player1 == app.current_player:
            self.player1.add_win()
            app.p1_wins +=1
        else:
            self.player2.add_win()
            app.p2_wins +=1
        print(self.game_end_event)

    def break_and_run(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player.name} broke and ran!"
        self.game_winner = app.current_player
        if self.player1 == app.current_player:
            self.player1.add_win()
            self.player1.balls_made += 8
            app.p1_wins +=1
        else:
            self.player2.add_win()
            self.player2.balls_made += 8
            app.p2_wins +=1
        print(self.game_end_event)


    def made_8_and_scratched(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player.name} made 8 ball but scratched!"
        if self.player1 == app.current_player:
            self.player2.add_win()
            app.p2_wins +=1
            self.game_winner = app.player2

        else:
            self.player1.add_win()
            app.p1_wins +=1
            app.current_player = app.player2
            self.game_winner = app.player1

        app.record_turn_time()
        app.turns += 1
        app.innings = app.turns // 2
        # this code has to run last in method!!!
        app.current_player = self.player2 if app.current_player == self.player1 else self.player1



    def get_game_results(self):
        buttons = [self.ids.eight_ball_break, self.ids.break_and_run, self.ids.scratched]
        if not any(btn.state == 'down' for btn in buttons):
            # Update the label instead of just printing
            self.ids.error_label.text = "Please select a reason before submitting."
            return  # Stop here so the popup stays open

        app = App.get_running_app()
        if self.ids.eight_ball_break.state == 'down':
            self.eight_ball_break()

        elif self.ids.break_and_run.state == 'down':
            self.break_and_run()

        elif self.ids.scratched.state == 'down':
            self.made_8_and_scratched()

        # 1. Create a structured entry for this match

        # get todays date and time for timestamp
        current_date = datetime.now().strftime("%m-%d-%Y")
        current_time = datetime.now().strftime('%I:%M:%S %p')
        print(current_date)
        print(current_time)

        # <-Added safety check to prevent KeyError if match_id is missing --->
        if current_date not in app.game_data:
            app.game_data[current_date] = {}

        if app.match_id not in app.game_data[current_date]:
            app.game_data[current_date][app.match_id] = {
                "match_id": app.match_id,
                "match_in_progress": True,
                "game_type": app.game_type,
                "games": []
            }

        match_container = app.game_data[current_date][app.match_id]

        # 1. Calculate rack time first using your turn data
        total_rack_seconds = sum(turn.get('turn_time', 0) for turn in app.turn_data)
        minutes, seconds = divmod(total_rack_seconds, 60)
        formatted_rack_time = f"{minutes:02}:{seconds:02}"

        game_entry = {
            "timestamp": current_time,
            "game": app.match_count,
            'rack_time': formatted_rack_time,
            "player1": {
                'name': app.player1.name,
                'user_id': app.player1.user_id,
                'balls_made': app.player1.balls_made
            },
            "player2": {
                'name': app.player2.name,
                'user_id': app.player2.user_id,
                'balls_made': app.player2.balls_made
            },
            "total_innings": len(app.turn_data) // 2,
            "match_winner": self.game_winner.name,
            "game_end_event": self.game_end_event,
            "turns": list(app.turn_data)
        }

        # Append your finished game entry
        match_container['games'].append(game_entry)

        match_container["player1_wins"] = app.p1_wins
        match_container["player2_wins"] = app.p2_wins
        match_container["player1_safes"] = app.p1_safe
        match_container["player2_safes"] = app.p2_safe
        # save match data to game_data dictionary on disk
        # 5. Notify Kivy that the property has changed
        app.game_data = app.game_data

        # 6. Save using the new method signature (with user_data_dir)
        try:
            app.save_data.save(app.game_data, app.user_data_dir)

            self.ids.error_label.text = "Match saved successfully!"
            self.ids.error_label.color = (0, 1, 0, 1)

            app.turn_data = []
            app.rack_turn_count = 0


            # Close after success
            Clock.schedule_once(self.close_popup, 1.5)
            app.start_timer()
        except:
            self.ids.error_label.text = "Match saved failed!"
            self.ids.error_label.color = (1, 0, 0, 1)  # Red

        #retrieve play again choice and trigger game end summary if user chooses 'no'
        if self.ids.yes.state == 'down':
            app.match_count += 1
            print(f'Now starting game {app.match_count}')
            # User wants to play another rack, so keep match_in_progress = True and set game_active = True for the next rack
            app.game_active = True
        else:
            print('Game Over!')
            print(f'Player 1 made {app.player1.balls_made} total balls')
            print(f'Player 2 made {app.player2.balls_made} total balls')
            app.match_in_progress = False
            app.game_active = False
            match_container["match_in_progress"] = False
            app.save_data.save(app.game_data, app.user_data_dir)
            self.show_popup()

    def close_popup(self, dt=None):
        self.dismiss()
