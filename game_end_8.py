from datetime import datetime
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.clock import Clock
from popups import GameEndSummary


#game end popup logic
class GameEndPopup(Popup):
    def __init__(self, player1, player2, **kwargs):
        super().__init__(**kwargs)
        self.player1 = player1
        self.player2 = player2
        self.game_end_event = ""
        self.game_winner = None
        self.selected_opp_ball = None
        self.selected_player_ball = None

    #popup function for game end summary
    def show_popup(self):
        popup = GameEndSummary()
        popup.open()

        # validate toggle function for play again.
    def validate_toggle(self, current_btn):
        if self.ids.yes.state == 'normal' and self.ids.no.state == 'normal':
            current_btn.state = 'down'


    def on_ball_toggle(self, button, state, group_type):
        """Automatically runs whenever any ball button is clicked."""
        if state == 'down':
            if group_type == 'opp_balls':
                self.selected_opp_ball = button.ball_value
                print(f'Oppenent had {self.selected_opp_ball} balls left!')
            elif group_type == 'player_balls':
                self.selected_player_ball = button.ball_value
                print(f'Current player had {self.selected_player_ball} balls left!')

    def made_8ball(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player.name} made 8ball"
        self.game_winner = app.current_player
        if self.player1 == app.current_player:
            self.player1.add_win()
            self.player1.balls_made += 1
            app.p1_wins +=1
        else:
            self.player2.add_win()
            self.player2.balls_made += 1
            app.p2_wins +=1

        print(self.game_end_event)


    def early_8(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player.name} made 8ball early!"
        if self.player1 == app.current_player:
            self.player2.add_win()
            app.p2_wins += 1
            self.game_winner = app.player2
        else:
            self.game_winner = app.player1
            self.player1.add_win()
            app.p1_wins += 1

        app.record_turn_time()
        app.turns += 1
        app.innings = app.turns // 2
        # this code has to run last in method!!!

        app.current_player = self.player2 if app.current_player == self.player1 else self.player1



    def made_8ball_wrong_pocket(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player.name} made 8ball wrong pocket"
        if self.player1 == app.current_player:
            self.player2.add_win()
            app.p2_wins +=1
            self.game_winner = app.player2
        else:
            self.game_winner = app.player1
            self.player1.add_win()
            app.p1_wins +=1

        app.record_turn_time()
        app.turns += 1
        app.innings = app.turns // 2
        # this code has to run last in method!!!

        app.current_player = self.player2 if app.current_player == self.player1 else self.player1

    def scratched_on_8ball(self):
        app = App.get_running_app()
        self.game_end_event = f"{app.current_player.name} scratched on 8ball"
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
        p2_balls_rem = self.selected_opp_ball
        # Capture player balls remaining if early 8 is toggled down, otherwise default to 0 (cleared/won) or handle as needed
        p1_balls_rem = self.selected_player_ball if self.ids.early_8.state == 'down' else 0

        buttons = [self.ids.made_8ball, self.ids.early_8, self.ids.wrong_pocket, self.ids.scratched]

        #error label for submitting without a game end choice
        if not any(btn.state == 'down' for btn in buttons):
            # Update the label instead of just printing
            self.ids.error_label.text = "Please select a reason before submitting."
            return  # Stop here so the popup stays open

        if self.selected_opp_ball is None:
            self.ids.error_label.text = "Please select opponent balls remaining!"
            return

        app = App.get_running_app()
        if self.ids.made_8ball.state == 'down':
            self.made_8ball()
        elif self.ids.early_8.state == 'down':
            self.early_8()

        elif self.ids.wrong_pocket.state == 'down':
            self.made_8ball_wrong_pocket()

        elif self.ids.scratched.state == 'down':
            self.scratched_on_8ball()


        # --- PLAYER OBJECT UPDATE LOGIC to record balls remaining history---
        current_shooter = app.current_player
        opponent_player = self.player2 if current_shooter == self.player1 else self.player1

        if p1_balls_rem is not None:
            current_shooter.update_balls_made(p1_balls_rem)

        if p2_balls_rem is not None:
            opponent_player.update_balls_made(p2_balls_rem)


        # 1. Create a structured entry for this match

        #get todays date and time for timestamp
        current_date= datetime.now().strftime("%m-%d-%Y")
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

        # --- Ensure match header keys are explicitly updated here ---
        match_container["player1_wins"] = app.p1_wins
        match_container["player2_wins"] = app.p2_wins
        match_container["player1_safes"] = app.p1_safe
        match_container["player2_safes"] = app.p2_safe
        match_container["match_in_progress"] = True
        match_container["game_type"] = app.game_type

        # 1. Calculate rack time first using your turn data
        total_rack_seconds = sum(turn.get('turn_time', 0) for turn in app.turn_data)
        minutes, seconds = divmod(total_rack_seconds, 60)
        formatted_rack_time = f"{minutes:02}:{seconds:02}"

        game_entry = {
                 "timestamp": current_time,
                "game": app.match_count,
                'rack_time': formatted_rack_time,
                "total_innings": len(app.turn_data) // 2,
                "match_winner": self.game_winner.name,
                "game_end_event": self.game_end_event,
                "player1" : {
                    'name': app.player1.name,
                    'user_id': app.player1.user_id,
                    'balls_made': app.player1.balls_made
                },
                "player2" : {
                    'name': app.player2.name,
                    'user_id': app.player2.user_id,
                    'balls_made': app.player2.balls_made
                },
                "turns": list(app.turn_data)
                }

        # Append your finished game entry
        match_container['games'].append(game_entry)

        match_container["player1_wins"] = app.p1_wins
        match_container["player2_wins"] = app.p2_wins
        match_container["player1_safes"] = app.p1_safe
        match_container["player2_safes"] = app.p2_safe

        #save match data to game_data dictionary on disk
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

        #revert remaining balls back to None
        self.selected_opp_ball = None
        self.selected_player_ball = None

        # retrieve play again choice and trigger game end summary if user chooses 'no'
        if self.ids.yes.state == 'down':
            # User wants to play another rack, so keep match_in_progress = True and set game_active = True for the next rack
            app.game_active = True
            app.match_count += 1
            print(f'Now starting game {app.match_count}')
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
