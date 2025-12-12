import os
import sys
import tkinter as tk
from tkinter import font as tkfont, messagebox, ttk
import StatsTracker
import copy 

def resource_path(relative_path):
    """
    Get absolute path to resource, works for development and for PyInstaller
    during run time when it extracts files to a temporary folder (_MEIPASS).
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Fallback for development (runs from current directory)
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class BasketballApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        try:
            # Ensure load_data is called before accessing game_data
            StatsTracker.load_data() 
        except AttributeError:
            messagebox.showerror("Initialization Error", "Could not initialize StatsTracker. Check if StatsTracker.py is in the directory.")
            self.destroy()
            return

        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        self.stat_font = tkfont.Font(family='Helvetica', size=10)
        self.mono_font = tkfont.Font(family='Courier New', size=10)
        self.title("Live Basketball Stats Tracker v4")
        self.geometry("1100x750") 
        self.minsize(900,600)

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        
        for F in (HomePage, ScoreboardPage, PlayerStatsPage, IntermissionPage, RosterManagementPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("HomePage") 

    def show_frame(self, page_name):
        """Show a frame and ensure its content is updated."""
        frame = self.frames[page_name]
        
        # Ensure data is updated on navigation
        if hasattr(frame, 'update_display'):
            frame.update_display()
            
        frame.tkraise()

    def reset_data(self):
        if messagebox.askyesno("Reset Confirmation", "Are you sure you want to RESET ALL GAME DATA? This action cannot be undone."):
            StatsTracker.reset_all_stats()
            self.frames['ScoreboardPage'].update_player_buttons() 
            self.show_frame("HomePage")

    def undo_action(self):
        if StatsTracker.undo_last_action():
            messagebox.showinfo("Undo Success", "Last action reverted.")
        else:
            messagebox.showinfo("Undo Failed", "Action history is empty or action failed to revert.")
        
        self.frames['HomePage'].update_display()
        self.frames['ScoreboardPage'].update_display()
        self.frames['PlayerStatsPage'].update_display()


# --- HOME PAGE ---
class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        tk.Label(self, text="Basketball Game Stats Tracker", 
                 font=controller.title_font).pack(side="top", fill="x", pady=10)
        
        self.score_label = tk.Label(self, text="", font=controller.title_font, fg="blue")
        self.score_label.pack(pady=20)
        
        self.quarter_label = tk.Label(self, text="", font=controller.stat_font, fg="gray")
        self.quarter_label.pack()

        tk.Button(self, text="Go to Live Scoreboard",
                  command=lambda: controller.show_frame("ScoreboardPage")).pack(pady=5)
        tk.Button(self, text="View Player Stats & Quarterly Breakdown",
                  command=lambda: controller.show_frame("PlayerStatsPage")).pack(pady=5)
        tk.Button(self, text="Intermission / Timeout Timer",
                  command=lambda: controller.show_frame("IntermissionPage")).pack(pady=5)
        tk.Button(self, text="Manage Reeths-Puffer Roster",
                  command=lambda: controller.show_frame("RosterManagementPage")).pack(pady=5)
                  
        tk.Button(self, text="↩️ UNDO LAST ACTION",
                  command=controller.undo_action,
                  fg="orange").pack(pady=20)
                  
        tk.Button(self, text="⚠️ RESET ALL STATS (Start New Game)",
                  command=controller.reset_data,
                  fg="red").pack(pady=40)
        
    def update_display(self):
        score = StatsTracker.get_current_score()
        quarter = StatsTracker.get_current_quarter()
        self.score_label.config(text=f"Reeths-Puffer: {score['Team1']} vs Team 2: {score['Team2']}")
        self.quarter_label.config(text=f"Current Period: {quarter}")


# --- ROSTER MANAGEMENT PAGE (Reeths-Puffer Only) ---
class RosterManagementPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        tk.Label(self, text="Reeths-Puffer Roster Management", 
                 font=controller.title_font).pack(side="top", fill="x", pady=10)
        
        # --- Input Frame ---
        input_frame = tk.LabelFrame(self, text="Add/Edit R-PHS Player", padx=10, pady=10)
        input_frame.pack(pady=10)
        
        tk.Label(input_frame, text="Name:").grid(row=0, column=0, sticky="w")
        self.name_entry = tk.Entry(input_frame)
        self.name_entry.grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(input_frame, text="Number:").grid(row=1, column=0, sticky="w")
        self.number_entry = tk.Entry(input_frame)
        self.number_entry.grid(row=1, column=1, padx=5, pady=2)
        
        self.starter_var = tk.BooleanVar(self)
        tk.Checkbutton(input_frame, text="Starter", variable=self.starter_var).grid(row=2, column=0, columnspan=2, pady=5)
        
        tk.Button(input_frame, text="Add/Update Player", command=self.add_or_update_player).grid(row=3, column=0, columnspan=2, pady=5)
        
        # --- Roster Display Frame ---
        tk.Label(self, text="Current Roster (RP # | Name | Starter)", font=controller.stat_font).pack(pady=5)
        self.canvas = tk.Canvas(self)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.roster_frame = tk.Frame(self.canvas)

        self.roster_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.roster_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="top", fill="both", expand=True, padx=10)
        self.scrollbar.pack(side="right", fill="y")
        
        tk.Button(self, text="Go to Home Page",
                  command=lambda: controller.show_frame("HomePage")).pack(pady=10)
                  
    def add_or_update_player(self):
        name = self.name_entry.get().strip()
        number_str = self.number_entry.get().strip()
        is_starter = self.starter_var.get()
        
        if not name:
            messagebox.showerror("Error", "Player name cannot be empty.")
            return
            
        try:
            number = int(number_str)
        except ValueError:
            messagebox.showerror("Error", "Player number must be an integer.")
            return

        StatsTracker.update_roster(name, 'Team1', number, is_starter)
        messagebox.showinfo("Success", f"Player '{name}' added/updated for Reeths-Puffer.")
        
        self.controller.frames['ScoreboardPage'].update_player_buttons() 
        self.update_display()
        self.name_entry.delete(0, tk.END)
        self.number_entry.delete(0, tk.END)
        self.starter_var.set(False)

    def load_player_for_edit(self, player_data):
        self.name_entry.delete(0, tk.END)
        self.number_entry.delete(0, tk.END)
        
        self.name_entry.insert(0, player_data['name'])
        self.number_entry.insert(0, str(player_data['number']))
        self.starter_var.set(player_data['starter'])
        
    def remove_player_prompt(self, player_name):
        if messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove '{player_name}'? All stats will be lost."):
            StatsTracker.remove_player(player_name)
            messagebox.showinfo("Removed", f"Player '{player_name}' removed.")
            
            self.controller.frames['ScoreboardPage'].update_player_buttons() 
            self.update_display()

    def update_display(self):
        for widget in self.roster_frame.winfo_children():
            widget.destroy()

        roster = StatsTracker.get_roster('Team1')
        
        for player in roster:
            player_row = tk.Frame(self.roster_frame, pady=2)
            player_row.pack(fill="x", padx=5)
            
            number_text = f"#{player['number']}"
            name_text = player['name']
            starter_text = "(Starter)" if player['starter'] else ""
            
            tk.Label(player_row, text=number_text, width=5, anchor='w').pack(side=tk.LEFT, padx=5)
            tk.Label(player_row, text=name_text, width=20, anchor='w', font=self.controller.stat_font).pack(side=tk.LEFT, padx=5)
            tk.Label(player_row, text=starter_text, width=10, anchor='w', fg='green').pack(side=tk.LEFT, padx=5)
            
            tk.Button(player_row, text="Edit", command=lambda p=player: self.load_player_for_edit(p), width=5).pack(side=tk.LEFT, padx=2)
            tk.Button(player_row, text="Remove", command=lambda n=player['name']: self.remove_player_prompt(n), width=7, fg='red').pack(side=tk.LEFT, padx=2)

        self.roster_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))


# --- SCOREBOARD PAGE ---
class ScoreboardPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # --- Top Section: Score, Quarter, and Control Buttons ---
        top_frame = tk.Frame(self)
        top_frame.pack(side="top", fill="x", pady=5, padx=10)
        
        # 1. Current Score Display
        score_frame = tk.Frame(top_frame)
        score_frame.pack(side=tk.LEFT, padx=5)
        tk.Label(score_frame, text="SCORE:", font=controller.title_font, fg="black").pack(side=tk.LEFT, padx=5)
        self.team1_label = tk.Label(score_frame, text="T1: 0", font=controller.title_font, fg="blue")
        self.team1_label.pack(side=tk.LEFT, padx=5)
        self.team2_label = tk.Label(score_frame, text="T2: 0", font=controller.title_font, fg="red")
        self.team2_label.pack(side=tk.LEFT, padx=15)
        
        # 2. Quarter Control
        quarter_control_frame = tk.Frame(top_frame)
        quarter_control_frame.pack(side=tk.LEFT, padx=20)
        self.current_q_label = tk.Label(quarter_control_frame, text="Q: Q1", font=controller.stat_font, fg="darkgreen")
        self.current_q_label.pack(side=tk.LEFT)
        
        tk.Button(quarter_control_frame, text="Next Q", command=self.advance_quarter).pack(side=tk.LEFT, padx=5)
        tk.Button(quarter_control_frame, text="Prev Q", command=self.previous_quarter).pack(side=tk.LEFT, padx=5)

        # 3. End of Quarter Score Input
        eoc_frame = tk.LabelFrame(top_frame, text="Set End-of-Period Score", padx=5, pady=2)
        eoc_frame.pack(side=tk.LEFT, padx=15)
        
        tk.Label(eoc_frame, text="T1:").pack(side=tk.LEFT)
        self.t1_eoc_entry = tk.Entry(eoc_frame, width=3)
        self.t1_eoc_entry.pack(side=tk.LEFT)
        
        tk.Label(eoc_frame, text="T2:").pack(side=tk.LEFT, padx=5)
        self.t2_eoc_entry = tk.Entry(eoc_frame, width=3)
        self.t2_eoc_entry.pack(side=tk.LEFT)
        
        tk.Button(eoc_frame, text="Record Score", command=self.record_eoc_score).pack(side=tk.LEFT, padx=5)

        # 4. Navigation Buttons
        tk.Button(top_frame, text="↩️ UNDO", command=controller.undo_action, fg="orange").pack(side=tk.RIGHT, padx=5)
        tk.Button(top_frame, text="🏠 Home", command=lambda: controller.show_frame("HomePage")).pack(side=tk.RIGHT, padx=5)


        # --- Main Stats Entry Section ---
        main_stats_frame = tk.Frame(self)
        main_stats_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        # A. Reeths-Puffer Player Stats (Left)
        self.team1_player_frame = self._create_stats_scroll_frame(main_stats_frame, "Reeths-Puffer Player Stats")
        self.team1_player_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # B. Team Totals & Team 2 Entry (Right Column)
        right_column_frame = tk.Frame(main_stats_frame)
        right_column_frame.pack(side="left", fill="y", padx=5)

        # B1. Total Team Stats Comparison
        self.team_comparison_frame = tk.LabelFrame(right_column_frame, text="Live Team Totals Comparison", padx=5, pady=5)
        self.team_comparison_frame.pack(fill="x", pady=5)
        self._create_team_comparison_display() # Initialize display labels

        # B2. Team Generic Stats (Reeths-Puffer Rebounds & Team 2 All)
        team_generic_container = tk.LabelFrame(right_column_frame, text="Team Generic & Team 2 Entry", padx=10, pady=5)
        team_generic_container.pack(fill="x", pady=5)
        
        self._create_team1_rebounds_row(team_generic_container)
        ttk.Separator(team_generic_container, orient=tk.HORIZONTAL).pack(fill='x', pady=5)
        self._create_team2_generic_stats_row(team_generic_container)

        self.update_player_buttons()
        self.update_display() # Initial display update

    # --- Quarter Navigation Logic ---
    def advance_quarter(self):
        current_q = StatsTracker.get_current_quarter()
        quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        
        try:
            current_index = quarters.index(current_q)
            if current_index < 3:
                next_q = quarters[current_index + 1]
                StatsTracker.set_current_quarter(next_q)
                messagebox.showinfo("Quarter Change", f"Advanced to {next_q}")
            else: # Must be Q4 or OT
                next_ot_num = StatsTracker.game_data['next_ot_num']
                next_q = f"OT{next_ot_num}"
                StatsTracker.set_current_quarter(next_q)
                messagebox.showinfo("Quarter Change", f"Advanced to {next_q}. Remember to record end of quarter score for Q4/OT.")
        except ValueError:
             # Handle advancing from OT
            if current_q.startswith('OT'):
                ot_num = int(current_q.replace('OT', ''))
                next_q = f"OT{ot_num + 1}"
                StatsTracker.set_current_quarter(next_q)
                messagebox.showinfo("Quarter Change", f"Advanced to {next_q}")
            else:
                messagebox.showerror("Error", "Cannot automatically determine next quarter.")
                
        self.update_display()
        self.controller.frames['PlayerStatsPage'].update_display()

    def previous_quarter(self):
        current_q = StatsTracker.get_current_quarter()
        quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        
        try:
            if current_q in quarters:
                current_index = quarters.index(current_q)
                if current_index > 0:
                    prev_q = quarters[current_index - 1]
                    StatsTracker.set_current_quarter(prev_q)
                    messagebox.showinfo("Quarter Change", f"Reverted to {prev_q}")
                else:
                    messagebox.showwarning("Warning", "Already in Q1. Cannot revert further.")
                    return
            elif current_q.startswith('OT'):
                ot_num = int(current_q.replace('OT', ''))
                if ot_num > 1:
                    prev_q = f"OT{ot_num - 1}"
                else:
                    prev_q = 'Q4'
                StatsTracker.set_current_quarter(prev_q)
                messagebox.showinfo("Quarter Change", f"Reverted to {prev_q}")
            else:
                messagebox.showerror("Error", "Cannot automatically determine previous quarter.")
        except Exception as e:
            messagebox.showerror("Error", f"Error reverting quarter: {e}")
            
        self.update_display()
        self.controller.frames['PlayerStatsPage'].update_display()

    def record_eoc_score(self):
        t1_score_str = self.t1_eoc_entry.get().strip()
        t2_score_str = self.t2_eoc_entry.get().strip()
        current_q = StatsTracker.get_current_quarter()
        
        try:
            t1_score = int(t1_score_str)
            t2_score = int(t2_score_str)
            
            # Simple check against current live score
            if t1_score < StatsTracker.game_data['team_score']['Team1'] or t2_score < StatsTracker.game_data['team_score']['Team2']:
                 messagebox.showwarning("Score Error", "Cumulative End-of-Quarter Score cannot be less than the current live score.")
                 return

            StatsTracker.set_end_of_quarter_score(current_q, t1_score, t2_score)
            
            messagebox.showinfo("Score Recorded", f"Cumulative score ({t1_score}-{t2_score}) recorded for end of {current_q}. Quarter score calculated.")
            
            self.t1_eoc_entry.delete(0, tk.END)
            self.t2_eoc_entry.delete(0, tk.END)
            
            self.update_display()
            self.controller.frames['PlayerStatsPage'].update_display()
            
        except ValueError:
            messagebox.showerror("Input Error", "Scores must be valid integers.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    # --- TEAM COMPARISON DISPLAY ---
    def _create_team_comparison_display(self):
        """Initializes the labels for the Team Totals Comparison frame."""
        self.t_labels = {}
        
        stat_keys = [
            'Points', 'Off_Rebounds', 'Def_Rebounds', 'Assists', 
            'Steals', 'Blocks', 'Turnovers', 'Fouls', 
            'FT_Made', 'FT_Attempted', 
            '2P_Made', '2P_Attempted', 
            '3P_Made', '3P_Attempted'
        ]
        
        # Header Row
        tk.Label(self.team_comparison_frame, text="STAT", font=self.controller.stat_font, width=15).grid(row=0, column=0)
        tk.Label(self.team_comparison_frame, text="R-P", font=self.controller.stat_font, width=5).grid(row=0, column=1)
        tk.Label(self.team_comparison_frame, text="T2", font=self.controller.stat_font, width=5).grid(row=0, column=2)
        
        # Data Rows
        for i, key in enumerate(stat_keys):
            row = i + 1
            display_text = key.replace('_', ' ').replace('Attempted', 'Att').replace('Made', 'M')
            
            tk.Label(self.team_comparison_frame, text=display_text, anchor='w', width=15).grid(row=row, column=0, sticky='w')
            
            # Label for Reeths-Puffer
            t1_label = tk.Label(self.team_comparison_frame, text="0", width=5)
            t1_label.grid(row=row, column=1)
            self.t_labels[f'T1_{key}'] = t1_label
            
            # Label for Team 2
            t2_label = tk.Label(self.team_comparison_frame, text="0", width=5)
            t2_label.grid(row=row, column=2)
            self.t_labels[f'T2_{key}'] = t2_label
            
    def _update_team_comparison_display(self):
        """Updates the values in the Team Totals Comparison frame."""
        t1_stats = StatsTracker.get_team_stats('Team1')
        t2_stats = StatsTracker.get_team_stats('Team2')
        
        keys_to_show = [
            'Points', 'Off_Rebounds', 'Def_Rebounds', 'Assists', 
            'Steals', 'Blocks', 'Turnovers', 'Fouls', 'FT_Made', 
            'FT_Attempted', '2P_Made', '2P_Attempted', '3P_Made', '3P_Attempted'
        ]
        
        for key in keys_to_show:
            t1_value = t1_stats.get(key, 0)
            t2_value = t2_stats.get(key, 0)
            
            self.t_labels[f'T1_{key}'].config(text=str(t1_value))
            self.t_labels[f'T2_{key}'].config(text=str(t2_value))

    # --- UTILITY AND OTHER ROWS ---

    def _clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def _create_stats_scroll_frame(self, parent, title):
        """Creates a scrollable frame structure for one team's stats entry."""
        container = tk.LabelFrame(parent, text=title, padx=5, pady=5)
        
        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        players_frame = tk.Frame(canvas)

        players_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=players_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        container.players_inner_frame = players_frame 
        container.canvas = canvas 
        return container

    def _create_team1_rebounds_row(self, parent):
        """Creates the row for Reeths-Puffer's team-level rebounds."""
        team1_rebound_frame = tk.LabelFrame(parent, text="R-PHS Rebounds (Non-Player)", padx=5, pady=5)
        team1_rebound_frame.pack(fill="x", pady=5)
        
        tk.Label(team1_rebound_frame, text="Team ORB/DRB:", width=18, anchor='w').pack(side=tk.LEFT)
        
        # Helper for Stat Buttons
        def create_stat_button(frame, text, stat_key, value):
            return tk.Button(frame, text=text, width=4, bg='lightblue',
                             command=lambda: self.update_team_generic_stat_and_refresh("Team1", stat_key, value))

        create_stat_button(team1_rebound_frame, "ORB", "Off_Rebounds", 1).pack(side=tk.LEFT, padx=1)
        create_stat_button(team1_rebound_frame, "DRB", "Def_Rebounds", 1).pack(side=tk.LEFT, padx=1)
        
        self.t1_orb_val = tk.Label(team1_rebound_frame, text="ORB: 0", width=6)
        self.t1_orb_val.pack(side=tk.LEFT, padx=5)
        self.t1_drb_val = tk.Label(team1_rebound_frame, text="DRB: 0", width=6)
        self.t1_drb_val.pack(side=tk.LEFT, padx=5)

    def _create_team2_generic_stats_row(self, parent):
        """Creates the row for Team 2's generic team stats."""
        team2_generic_frame = tk.LabelFrame(parent, text="Team 2 Generic Stats", padx=5, pady=5)
        team2_generic_frame.pack(fill="x", pady=5)
        
        tk.Label(team2_generic_frame, text="Team 2 Stats:", width=18, anchor='w', font=self.controller.stat_font).pack(side=tk.LEFT)
        
        # Helper for Team 2 Scoring/Shooting Buttons 
        def create_shot_button(frame, text, stat_key, value, color='pink'):
            return tk.Button(frame, text=text, width=4, bg=color,
                             command=lambda: self.update_team_generic_stat_and_refresh("Team2", stat_key, value))

        # MADE SHOTS (Scoring)
        create_shot_button(team2_generic_frame, "+FT", "FT_Made", 1, 'lightgreen').pack(side=tk.LEFT, padx=1)
        create_shot_button(team2_generic_frame, "+2P", "2P_Made", 1, 'lightgreen').pack(side=tk.LEFT, padx=1)
        create_shot_button(team2_generic_frame, "+3P", "3P_Made", 1, 'lightgreen').pack(side=tk.LEFT, padx=1)
        
        # MISSED SHOTS (Attempted Only)
        create_shot_button(team2_generic_frame, "FT A", "FT_Attempted", 1, 'lightcoral').pack(side=tk.LEFT, padx=1)
        create_shot_button(team2_generic_frame, "2P A", "2P_Attempted", 1, 'lightcoral').pack(side=tk.LEFT, padx=1)
        create_shot_button(team2_generic_frame, "3P A", "3P_Attempted", 1, 'lightcoral').pack(side=tk.LEFT, padx=1)
        
        # Helper for Team 2 Other Stats
        def create_stat_button(frame, text, stat_key, value):
            return tk.Button(frame, text=text, width=4, bg='#ffe0e0',
                             command=lambda: self.update_team_generic_stat_and_refresh("Team2", stat_key, value))

        create_stat_button(team2_generic_frame, "ORB", "Off_Rebounds", 1).pack(side=tk.LEFT, padx=1)
        create_stat_button(team2_generic_frame, "DRB", "Def_Rebounds", 1).pack(side=tk.LEFT, padx=1)
        create_stat_button(team2_generic_frame, "A", "Assists", 1).pack(side=tk.LEFT, padx=1)
        create_stat_button(team2_generic_frame, "STL", "Steals", 1).pack(side=tk.LEFT, padx=1)
        create_stat_button(team2_generic_frame, "BLK", "Blocks", 1).pack(side=tk.LEFT, padx=1)
        create_stat_button(team2_generic_frame, "TO", "Turnovers", 1).pack(side=tk.LEFT, padx=1)
        create_stat_button(team2_generic_frame, "F", "Fouls", 1).pack(side=tk.LEFT, padx=1)

    def update_player_buttons(self):
        self._clear_frame(self.team1_player_frame.players_inner_frame)
        
        # Helper to create buttons for a single player
        def create_player_row(parent_frame, player_data):
            player_name = player_data['name']
            
            player_row = tk.Frame(parent_frame)
            player_row.pack(fill="x", pady=2, padx=2)
            
            display_name = f"#{player_data['number']} {player_name}"
            tk.Label(player_row, text=display_name, width=15, anchor='w', font=self.controller.stat_font).pack(side=tk.LEFT, padx=2)
            
            # Helper for Stat Buttons
            def create_stat_button(parent, text, stat_key, value, player_name, color=None):
                btn = tk.Button(parent, text=text, width=4, 
                                 command=lambda: self.update_player_stat_and_refresh(player_name, stat_key, value))
                if color: btn.config(bg=color)
                return btn

            # Scoring/Shooting Stats (Made/Missed)
            create_stat_button(player_row, "FT M", "FT_Made", 1, player_name, 'lightgreen').pack(side=tk.LEFT, padx=1)
            create_stat_button(player_row, "FT A", "FT_Attempted", 1, player_name, 'lightcoral').pack(side=tk.LEFT, padx=1)
            create_stat_button(player_row, "2P M", "2P_Made", 1, player_name, 'lightgreen').pack(side=tk.LEFT, padx=1)
            create_stat_button(player_row, "2P A", "2P_Attempted", 1, player_name, 'lightcoral').pack(side=tk.LEFT, padx=1)
            create_stat_button(player_row, "3P M", "3P_Made", 1, player_name, 'lightgreen').pack(side=tk.LEFT, padx=1)
            create_stat_button(player_row, "3P A", "3P_Attempted", 1, player_name, 'lightcoral').pack(side=tk.LEFT, padx=1)

            # Other Stats
            create_stat_button(player_row, "ORB", "Off_Rebounds", 1, player_name, 'lightblue').pack(side=tk.LEFT, padx=1)
            create_stat_button(player_row, "DRB", "Def_Rebounds", 1, player_name, 'lightblue').pack(side=tk.LEFT, padx=1)
            create_stat_button(player_row, "A", "Assists", 1, player_name).pack(side=tk.LEFT, padx=1)
            create_stat_button(player_row, "STL", "Steals", 1, player_name).pack(side=tk.LEFT, padx=1)
            create_stat_button(player_row, "BLK", "Blocks", 1, player_name).pack(side=tk.LEFT, padx=1)
            create_stat_button(player_row, "TO", "Turnovers", 1, player_name, 'orange').pack(side=tk.LEFT, padx=1)
            create_stat_button(player_row, "F", "Fouls", 1, player_name, 'red').pack(side=tk.LEFT, padx=1)


        team1_players = StatsTracker.get_roster("Team1")
        team1_players.sort(key=lambda p: p['number'])
        
        for player in team1_players:
            create_player_row(self.team1_player_frame.players_inner_frame, player)
            
        self.team1_player_frame.players_inner_frame.update_idletasks()
        self.team1_player_frame.canvas.config(scrollregion=self.team1_player_frame.canvas.bbox("all"))

    def update_player_stat_and_refresh(self, player_name, stat_key, value):
        StatsTracker.update_player_stat(player_name, stat_key, value)
        self.update_display() 

    def update_team_generic_stat_and_refresh(self, team_name, stat_key, value):
        StatsTracker.update_team_generic_stat(team_name, stat_key, value)
        self.update_display()
        
    def update_display(self):
        score = StatsTracker.get_current_score()
        current_q = StatsTracker.get_current_quarter()
        
        self.team1_label.config(text=f"T1: {score['Team1']}")
        self.team2_label.config(text=f"T2: {score['Team2']}")
        self.current_q_label.config(text=f"Q: {current_q}")
        
        # Update Reeths-Puffer Team Rebounds display (using full team stats for accurate count)
        t1_team_rebounds = StatsTracker.get_team_stats('Team1')
        # We display the *team* portion of rebounds, not the total, as the total is in the comparison table.
        # Note: StatsTracker.get_team_stats('Team1') returns the SUM of player+team rebounds.
        # To get the Team portion, we need to access the raw data (a minor inconsistency, but acceptable here).
        raw_team_rebounds = StatsTracker.game_data['team1_team_rebounds'] 
        self.t1_orb_val.config(text=f"ORB: {raw_team_rebounds.get('Off_Rebounds', 0)}")
        self.t1_drb_val.config(text=f"DRB: {raw_team_rebounds.get('Def_Rebounds', 0)}")
        
        # Update Team Totals Comparison
        self._update_team_comparison_display()
        self.controller.frames['HomePage'].update_display()


# --- PLAYER STATS PAGE ---
class PlayerStatsPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        self.mono_font = controller.mono_font
        
        tk.Label(self, text="Reeths-Puffer Detailed Player Standings", font=controller.title_font).pack(side="top", fill="x", pady=10)
        
        # --- QUARTERLY SCORE BREAKDOWN ---
        self.quarterly_frame = tk.LabelFrame(self, text="Quarterly Score Breakdown (Q-Score [Cumulative Score])", padx=5, pady=5)
        self.quarterly_frame.pack(fill='x', padx=10, pady=10)
        self.quarter_labels = []

        # --- PLAYER STATS SCROLLABLE AREA ---
        tk.Label(self, text="Reeths-Puffer Player Stats:", font=controller.stat_font).pack(side="top", fill="x", pady=5)
        self.canvas = tk.Canvas(self)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="top", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.results_labels = []

        # Team 2 Summary at the bottom
        self.team2_summary_label = tk.Label(self, text="", font=controller.stat_font, justify=tk.LEFT)
        self.team2_summary_label.pack(side="top", fill="x", pady=10)

        tk.Button(self, text="Go to Home Page",
                  command=lambda: controller.show_frame("HomePage")).pack(pady=20)

    def _update_quarterly_breakdown(self):
        # Clear previous quarter labels
        for label in self.quarter_labels:
            label.destroy()
        self.quarter_labels = []
        
        breakdown = StatsTracker.get_quarterly_score_breakdown()
        
        if not breakdown:
             tk.Label(self.quarterly_frame, text="No quarter scores recorded yet.", fg="gray").pack()
             return

        # Header
        header_text = f"{'Period':<10}{'RP Score':<12}{'T2 Score':<12}"
        header = tk.Label(self.quarterly_frame, text=header_text, font=self.mono_font, anchor='w', bg="#e0e0e0")
        header.pack(fill='x', padx=5, pady=2)
        self.quarter_labels.append(header)
        
        current_q_label = StatsTracker.get_current_quarter()
        total1 = 0
        total2 = 0
        
        for item in breakdown:
            total1 += item['score1']
            total2 += item['score2']
            
            # Format: Q1: 20-18 [20-18]
            display_text = (
                f"{item['label']:<10}"
                f"{item['score1']}-{item['score2']} "
                f"[{item['cumulative1']}-{item['cumulative2']}]"
            )
            
            label = tk.Label(self.quarterly_frame, text=display_text, anchor='w', font=self.mono_font)
            
            # Highlight the current quarter
            if item['label'] == current_q_label:
                label.config(fg="blue", font=tkfont.Font(family='Courier New', size=10, weight="bold"))
                
            label.pack(fill='x', padx=5)
            self.quarter_labels.append(label)
            
        # Total Row
        ttk.Separator(self.quarterly_frame, orient=tk.HORIZONTAL).pack(fill='x', pady=2)
        total_text = f"TOTALS:  {StatsTracker.game_data['team_score']['Team1']}-{StatsTracker.game_data['team_score']['Team2']}"
        total_label = tk.Label(self.quarterly_frame, text=total_text, font=tkfont.Font(family='Courier New', size=10, weight="bold"), anchor='w')
        total_label.pack(fill='x', padx=5)
        self.quarter_labels.append(total_label)


    def update_display(self):
        # 1. Update Quarterly Breakdown
        self._update_quarterly_breakdown()
        
        # 2. Clear and update Player Stats
        for label in self.results_labels:
            label.destroy()
        self.results_labels = []

        standings = StatsTracker.get_player_data()
        standings.sort(key=lambda item: (-item['Points'], -item['Assists'], -item['Def_Rebounds']))
        
        # Player Header
        header_text = (
            f"{'#':<3}"
            f"{'Player Name':<18}"
            f"{'PTS':>5}"
            f"{'A':>4}"
            f"{'STL':>4}"
            f"{'BLK':>4}"
            f"{'TO':>4}"
            f"{'Fouls':>5}"
            f"{'ORB':>4}"
            f"{'DRB':>4}"
            f"{'FT%':>5}"
            f"{'2P%':>5}"
            f"{'3P%':>5}"
        )
        header = tk.Label(self.scrollable_frame, 
                          text=header_text, 
                          font=self.mono_font, 
                          anchor='w', bg="#e0e0e0")
        header.pack(fill='x', padx=5, pady=5)
        self.results_labels.append(header)
        
        # Player Data
        for stats in standings:
            bg_color = "#f0f0ff" if stats['starter'] else "white" 
            
            text = (
                f"{stats['number']:<3}"
                f"{stats['name'][:17]:<18}"
                f"{stats['Points']:>5}"
                f"{stats['Assists']:>4}"
                f"{stats['Steals']:>4}"
                f"{stats['Blocks']:>4}"
                f"{stats['Turnovers']:>4}"
                f"{stats['Fouls']:>5}"
                f"{stats['Off_Rebounds']:>4}"
                f"{stats['Def_Rebounds']:>4}"
                f"{stats['FT_PCT']:>5.1f}"
                f"{stats['2P_PCT']:>5.1f}"
                f"{stats['3P_PCT']:>5.1f}"
            )
            label = tk.Label(self.scrollable_frame, text=text, anchor='w', font=self.mono_font, bg=bg_color)
            label.pack(fill='x', padx=5)
            self.results_labels.append(label)
        
        self.scrollable_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        # 3. TEAM 2 GENERIC STATS Summary
        team2_stats = StatsTracker.get_team_stats('Team2')
        
        def calculate_team_pct(made_key, attempted_key):
            made = team2_stats.get(made_key, 0)
            attempted = team2_stats.get(attempted_key, 0)
            return round(made / attempted * 100, 1) if attempted > 0 else 0.0

        ft_pct = calculate_team_pct('FT_Made', 'FT_Attempted')
        twop_pct = calculate_team_pct('2P_Made', '2P_Attempted')
        threep_pct = calculate_team_pct('3P_Made', '3P_Attempted')
        
        t2_summary = (
            f"--- Team 2 Summary ---\n"
            f"PTS: {team2_stats.get('Points', 0)} | "
            f"FGM/A (FT/2P/3P): "
            f"{team2_stats.get('FT_Made', 0)}/{team2_stats.get('FT_Attempted', 0)} ({ft_pct}%) | "
            f"{team2_stats.get('2P_Made', 0)}/{team2_stats.get('2P_Attempted', 0)} ({twop_pct}%) | "
            f"{team2_stats.get('3P_Made', 0)}/{team2_stats.get('3P_Attempted', 0)} ({threep_pct}%)\n"
            f"REB (O/D): {team2_stats.get('Off_Rebounds', 0)}/{team2_stats.get('Def_Rebounds', 0)} | "
            f"AST: {team2_stats.get('Assists', 0)} | "
            f"STL: {team2_stats.get('Steals', 0)} | "
            f"BLK: {team2_stats.get('Blocks', 0)} | "
            f"TO: {team2_stats.get('Turnovers', 0)} | "
            f"Fouls: {team2_stats.get('Fouls', 0)}"
        )
        self.team2_summary_label.config(text=t2_summary, bg="#f5e0e0")


# --- INTERMISSION PAGE ---
class IntermissionPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        # Define time options in seconds
        self.time_options = {
            "Game Intermission (20:00)": 1200,
            "Halftime (10:00)": 600,
            "Full Timeout (1:00)": 60,
            "Half Timeout (0:30)": 30,
        }
        
        # Initialize time variables
        self.time_start = 0 
        self.time_left_s = 0
        self.timer_id = None    
        
        # Image map logic is kept but requires images in the directory
        self.image_map = {
            'Squirtle': {"threshold": 1200 / 2, "file": "Squirtle.png"},
            'Wartortle': {"threshold": 30, "file": "Wartortle.png"},
            'Blastoise': {"threshold": 0, "file": "Blastoise.png"},
        }
        self.current_image_ref = None 

        tk.Label(self, text="Intermission / Timeout", font=controller.title_font).pack(side="top", fill="x", pady=10)
        self.timer_label = tk.Label(self, text=self._format_time(), font=controller.title_font, fg="red")
        self.timer_label.pack(pady=10)
        self.image_label = tk.Label(self)
        self.image_label.pack()

        # Create buttons dynamically from time options
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        
        for text, time_s in self.time_options.items():
            tk.Button(button_frame, text=text, 
                      command=lambda t=time_s: self.start_timer(t)).pack(side=tk.LEFT, padx=5, pady=5)
                  
        tk.Button(self, text="Go to Home Page (Stop Timer)",
                  command=lambda: self._stop_timer_and_navigate("HomePage")).pack(pady=20)
                  
    def start_timer(self, start_time_s):
        """Starts the timer with a specified time in seconds."""
        if self.timer_id:
            self.after_cancel(self.timer_id)
            
        self.time_start = start_time_s # Set the new starting time
        self.time_left_s = start_time_s
        self.update_timer()

    def _update_image(self):
        """Updates the Pokemon image based on the time remaining."""
        image_file = None
        
        # If timer is short (<= 60s), use a smaller Blastoise threshold (5 seconds)
        # Otherwise (for 10m/20m), use 30 seconds
        blastoise_threshold = 5 if self.time_start <= 60 else 30 
        
        if self.time_left_s <= 0:
            image_file = self.image_map['Blastoise']['file']
        elif self.time_left_s <= blastoise_threshold:
            image_file = self.image_map['Blastoise']['file']
        elif self.time_left_s <= self.time_start / 2:
            image_file = self.image_map['Wartortle']['file']
        else:
            image_file = self.image_map['Squirtle']['file']
        
        try:
            # NOTE: If this fails, it's because you don't have the image files in your directory.
            new_image_ref = tk.PhotoImage(file=resource_path(image_file))
            self.image_label.config(image=new_image_ref)
            self.current_image_ref = new_image_ref
        except tk.TclError:
            self.image_label.config(image='', text=f"Error: {image_file} not found")
            self.current_image_ref = None

    def update_timer(self):
        """Decrements the timer and schedules the next update."""
        if self.time_left_s > 0:
            self.time_left_s -= 1
            self.timer_label.config(text=self._format_time())
            
            self._update_image()
            
            # Schedule this function to run again after 1000ms (1 second)
            self.timer_id = self.after(1000, self.update_timer)
        else:
            # Timer is done!
            self.timer_label.config(text="Time's Up!", fg="blue")
            self._update_image() # Final image update
            
    def _format_time(self):
        """Converts seconds into MM:SS format."""
        minutes = self.time_left_s // 60
        seconds = self.time_left_s % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _stop_timer_and_navigate(self, page_name):
        if self.timer_id:
            self.after_cancel(self.timer_id)
        self.controller.show_frame(page_name)


if __name__ == "__main__":    
    app = BasketballApp()
    app.mainloop()