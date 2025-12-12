import json
import os
import copy 

# --- CONFIGURATION ---
STATS_FILE = "basketball_stats.json"
HISTORY_FILE = "action_history.json"
MAX_HISTORY = 50 

# Detailed stat keys for Team 1 players
STAT_KEYS_T1 = [
    "FT_Made", "FT_Attempted", "2P_Made", "2P_Attempted", "3P_Made", "3P_Attempted",
    "Points", 
    "Off_Rebounds", "Def_Rebounds", "Assists", "Steals", "Blocks", "Turnovers", "Fouls"
]

# Generic team stats for Team 2 (and some Team 1 team stats)
# Includes makes/attempts for accurate display in team comparison table
TEAM_STAT_KEYS = [
    "Points", "Off_Rebounds", "Def_Rebounds", "Assists", 
    "Steals", "Blocks", "Turnovers", "Fouls",
    "FT_Made", "FT_Attempted", "2P_Made", "2P_Attempted", "3P_Made", "3P_Attempted"
]

# Scoring and dependency map for shots made
SCORING_MAP = {
    "FT_Made": {"points": 1, "attempt_key": "FT_Attempted"},
    "2P_Made": {"points": 2, "attempt_key": "2P_Attempted"},
    "3P_Made": {"points": 3, "attempt_key": "3P_Attempted"},
}

# Global Data Structures
game_data = {}
action_history = [] 

DEFAULT_T1_PLAYERS = [
    {'name': "Player A", 'team': 'Team1', 'number': 1, 'starter': True},
    {'name': "Player B", 'team': 'Team1', 'number': 5, 'starter': True},
]

# Initial Quarterly Score Structure
QUARTER_STRUCTURE = {
    'Q1': {'Team1': 0, 'Team2': 0, 'Cumulative1': 0, 'Cumulative2': 0},
    'Q2': {'Team1': 0, 'Team2': 0, 'Cumulative1': 0, 'Cumulative2': 0},
    'Q3': {'Team1': 0, 'Team2': 0, 'Cumulative1': 0, 'Cumulative2': 0},
    'Q4': {'Team1': 0, 'Team2': 0, 'Cumulative1': 0, 'Cumulative2': 0},
}

DEFAULT_STATS = {
    'roster': {'Team1': DEFAULT_T1_PLAYERS},
    'player_stats': {}, 
    'team_score': {'Team1': 0, 'Team2': 0},
    'team1_team_rebounds': {k: 0 for k in ["Off_Rebounds", "Def_Rebounds"]},
    'team2_generic_stats': {k: 0 for k in TEAM_STAT_KEYS},
    'current_quarter': 'Q1',
    'quarterly_scores': copy.deepcopy(QUARTER_STRUCTURE),
    'next_ot_num': 1 
}


# --- HISTORY & PERSISTENCE ---

def save_data():
    """Saves current game data to a JSON file."""
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(game_data, f, indent=4)
    except Exception as e:
        print(f"Error saving stats data: {e}")

def load_data():
    """Loads game data from a JSON file, or initializes defaults."""
    global game_data, action_history
    
    is_loaded = False
    temp_data = {}
    
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                temp_data = json.load(f)
                is_loaded = True
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error reading stats file: {e}. Starting with default data.")

    required_keys = ['roster', 'player_stats', 'team_score', 'team1_team_rebounds', 'team2_generic_stats', 'current_quarter', 'quarterly_scores', 'next_ot_num']
    
    if is_loaded and all(key in temp_data for key in required_keys):
        game_data = temp_data
    else:
        if is_loaded:
            print("Loaded data is corrupted/incomplete. Reverting to default data.")
        game_data = copy.deepcopy(DEFAULT_STATS)
        save_data() 

    # Load History (Optional)
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                action_history = json.load(f)
        else:
            action_history = []
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading history: {e}. Starting with empty history.")
        action_history = []

    _recalculate_all_scores()

def _push_history():
    """Saves a snapshot of the current state before an action."""
    global action_history
    snapshot = copy.deepcopy(game_data)
    action_history.append(snapshot)
    
    if len(action_history) > MAX_HISTORY:
        action_history.pop(0)
    
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(action_history, f, indent=4)
    except Exception as e:
        print(f"Error saving history data: {e}")


def undo_last_action():
    """Reverts the game state to the previous snapshot."""
    global game_data, action_history
    if action_history:
        previous_state = action_history.pop()
        game_data = previous_state
            
        save_data()
        return True
    return False

def reset_all_stats():
    """Resets all game data and clears history."""
    global game_data, action_history
    game_data = copy.deepcopy(DEFAULT_STATS)
    action_history = []
    
    if os.path.exists(STATS_FILE):
        os.remove(STATS_FILE)
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    
    _recalculate_all_scores() 
    save_data()


# --- SCORE CALCULATION LOGIC ---

def _recalculate_player_score(player_name):
    """Calculates points and updates attempts for a single player."""
    stats = game_data['player_stats'].get(player_name, {})
    
    total_points = 0
    total_points += stats.get('FT_Made', 0) * SCORING_MAP['FT_Made']['points']
    total_points += stats.get('2P_Made', 0) * SCORING_MAP['2P_Made']['points']
    total_points += stats.get('3P_Made', 0) * SCORING_MAP['3P_Made']['points']
    
    # Ensure attempts are at least as high as makes
    for key, val in SCORING_MAP.items():
        made = stats.get(key, 0)
        attempt_key = val['attempt_key']
        stats[attempt_key] = max(stats.get(attempt_key, 0), made)
    
    stats['Points'] = total_points
    game_data['player_stats'][player_name] = stats
    return total_points


def _recalculate_all_scores():
    """Recalculates scores for all teams and players."""
    
    total_t1_score = 0
    
    for player in game_data['roster']['Team1']:
        total_t1_score += _recalculate_player_score(player['name'])

    total_t2_score = game_data['team2_generic_stats'].get('Points', 0)

    game_data['team_score']['Team1'] = total_t1_score
    game_data['team_score']['Team2'] = total_t2_score


# --- QUARTER AND SCORE MANAGEMENT ---

def get_current_quarter():
    """Returns the current quarter label (e.g., 'Q1', 'OT1')."""
    return game_data.get('current_quarter', 'Q1')

def set_current_quarter(quarter_label):
    """Sets the current quarter label."""
    _push_history()
    game_data['current_quarter'] = quarter_label
    save_data()

def set_end_of_quarter_score(quarter_label, t1_cumulative_score, t2_cumulative_score):
    """
    Records the final cumulative score at the end of a quarter, 
    calculates the quarter's score, and prepares for the next quarter.
    """
    _push_history()
    
    quarter_data = game_data['quarterly_scores'].get(quarter_label)
    if not quarter_data:
        # Handle new overtime period creation if needed
        if quarter_label.startswith('OT'):
            game_data['quarterly_scores'][quarter_label] = copy.deepcopy(QUARTER_STRUCTURE['Q1']) 
        
        quarter_data = game_data['quarterly_scores'].get(quarter_label)
        if not quarter_data:
             print(f"Error: Could not find or create structure for {quarter_label}")
             return 

    # 1. Determine Previous Cumulative Score
    quarter_keys = list(game_data['quarterly_scores'].keys())
    q_index = quarter_keys.index(quarter_label)
    
    if q_index > 0:
        prev_q_key = quarter_keys[q_index - 1]
        prev_cumulative_t1 = game_data['quarterly_scores'][prev_q_key]['Cumulative1']
        prev_cumulative_t2 = game_data['quarterly_scores'][prev_q_key]['Cumulative2']
    else:
        prev_cumulative_t1 = 0
        prev_cumulative_t2 = 0
        
    # 2. Calculate Quarter Score
    q_score_t1 = t1_cumulative_score - prev_cumulative_t1
    q_score_t2 = t2_cumulative_score - prev_cumulative_t2
    
    # 3. Update Data Structure
    quarter_data['Cumulative1'] = t1_cumulative_score
    quarter_data['Cumulative2'] = t2_cumulative_score
    quarter_data['Team1'] = q_score_t1
    quarter_data['Team2'] = q_score_t2
    
    # 4. Check for and update next OT number
    if quarter_label.startswith('OT'):
        ot_num = int(quarter_label.replace('OT', ''))
        if ot_num == game_data['next_ot_num']:
            game_data['next_ot_num'] += 1
    
    save_data()

def get_quarterly_score_breakdown():
    """Returns the ordered list of quarterly score data."""
    # Ensure standard quarters are first, followed by OT in order
    keys = list(game_data['quarterly_scores'].keys())
    standard_keys = [k for k in keys if k.startswith('Q') and len(k) == 2]
    ot_keys = [k for k in keys if k.startswith('OT')]
    
    standard_keys.sort() 
    ot_keys.sort(key=lambda x: int(x.replace('OT', ''))) 
    
    ordered_keys = standard_keys + ot_keys
    
    breakdown = []
    for key in ordered_keys:
        breakdown.append({
            'label': key,
            'score1': game_data['quarterly_scores'][key]['Team1'],
            'score2': game_data['quarterly_scores'][key]['Team2'],
            'cumulative1': game_data['quarterly_scores'][key]['Cumulative1'],
            'cumulative2': game_data['quarterly_scores'][key]['Cumulative2']
        })
            
    return breakdown


# --- PRIMARY UPDATE FUNCTIONS ---

def update_player_stat(player_name, stat_key, value):
    """Updates a single stat for a player."""
    _push_history() 
    
    if player_name not in game_data['player_stats']:
        game_data['player_stats'][player_name] = {k: 0 for k in STAT_KEYS_T1}

    current_val = game_data['player_stats'][player_name].get(stat_key, 0)
    game_data['player_stats'][player_name][stat_key] = current_val + value
    
    if stat_key in SCORING_MAP and stat_key.endswith('_Made'):
        attempt_key = SCORING_MAP[stat_key]['attempt_key']
        attempt_val = game_data['player_stats'][player_name].get(attempt_key, 0)
        game_data['player_stats'][player_name][attempt_key] = attempt_val + value

    _recalculate_all_scores()
    save_data()

def update_team_generic_stat(team_name, stat_key, value):
    """Updates a generic stat for Team 1 (rebounds) or all stats for Team 2."""
    _push_history() 
    
    if team_name == 'Team1':
        current_val = game_data['team1_team_rebounds'].get(stat_key, 0)
        game_data['team1_team_rebounds'][stat_key] = current_val + value
    
    elif team_name == 'Team2':
        current_val = game_data['team2_generic_stats'].get(stat_key, 0)
        game_data['team2_generic_stats'][stat_key] = current_val + value
        
        # Only update points if a MADE shot stat is logged
        if stat_key in SCORING_MAP and stat_key.endswith('_Made'):
            points = SCORING_MAP[stat_key]['points'] * value
            current_points = game_data['team2_generic_stats'].get('Points', 0)
            game_data['team2_generic_stats']['Points'] = current_points + points
            
        # Ensure attempts are at least as high as makes for T2
        if stat_key in SCORING_MAP and stat_key.endswith('_Made'):
            attempt_key = SCORING_MAP[stat_key]['attempt_key']
            made = game_data['team2_generic_stats'].get(stat_key, 0)
            attempted = game_data['team2_generic_stats'].get(attempt_key, 0)
            game_data['team2_generic_stats'][attempt_key] = max(attempted, made)
            
    _recalculate_all_scores()
    save_data()


def update_roster(name, team, number, is_starter):
    """Adds or updates a player in the roster."""
    _push_history()
    
    new_player = {'name': name, 'team': team, 'number': number, 'starter': is_starter}
    
    roster_list = game_data['roster'].get(team, [])
    
    # Check if player already exists (by name)
    found = False
    for i, player in enumerate(roster_list):
        if player['name'] == name:
            roster_list[i] = new_player
            found = True
            break
            
    if not found:
        roster_list.append(new_player)
        
    game_data['roster'][team] = roster_list
    
    # Initialize stats if this is a new player
    if name not in game_data['player_stats']:
        game_data['player_stats'][name] = {k: 0 for k in STAT_KEYS_T1}
    
    save_data()

def remove_player(player_name):
    """Removes a player from the roster and clears their stats."""
    _push_history()
    
    roster_list = game_data['roster'].get('Team1', [])
    game_data['roster']['Team1'] = [p for p in roster_list if p['name'] != player_name]
    
    if player_name in game_data['player_stats']:
        del game_data['player_stats'][player_name]
        
    _recalculate_all_scores()
    save_data()


# --- DATA RETRIEVAL FUNCTIONS ---

def _safe_percentage(made, attempted):
    """Calculates percentage, returning 0.0 if attempted is zero."""
    return round(made / attempted * 100, 1) if attempted > 0 else 0.0

def get_player_data():
    """Compiles detailed, calculated stats for all Team 1 players."""
    data = []
    
    for player in game_data['roster']['Team1']:
        stats = game_data['player_stats'].get(player['name'], {}) 

        # Retrieve/Calculate fields needed for GUI display
        ft_att = stats.get('FT_Attempted', 0)
        twop_att = stats.get('2P_Attempted', 0)
        threep_att = stats.get('3P_Attempted', 0)

        ft_made = stats.get('FT_Made', 0)
        twop_made = stats.get('2P_Made', 0)
        threep_made = stats.get('3P_Made', 0)

        ft_pct = _safe_percentage(ft_made, ft_att)
        twop_pct = _safe_percentage(twop_made, twop_att)
        threep_pct = _safe_percentage(threep_made, threep_att)

        data.append({
            'name': player['name'],
            'team': player['team'],
            'number': player['number'],
            'starter': player['starter'],
            'Points': stats.get('Points', 0),
            'Assists': stats.get('Assists', 0),
            'Steals': stats.get('Steals', 0),
            'Blocks': stats.get('Blocks', 0),
            'Turnovers': stats.get('Turnovers', 0),
            'Fouls': stats.get('Fouls', 0),
            'Off_Rebounds': stats.get('Off_Rebounds', 0),
            'Def_Rebounds': stats.get('Def_Rebounds', 0),
            'FT_PCT': ft_pct,
            '2P_PCT': twop_pct,
            '3P_PCT': threep_pct,
            'FT_Made': ft_made, 'FT_Attempted': ft_att,
            '2P_Made': twop_made, '2P_Attempted': twop_att,
            '3P_Made': threep_made, '3P_Attempted': threep_att
        })
    return data

def get_current_score():
    return game_data['team_score']
    
def get_team_stats(team_name):
    """Retrieves aggregated stats for Team 1 or generic stats for Team 2."""
    if team_name == 'Team1':
        # To get the full team stats for Team 1, we must sum player stats and team rebounds.
        # Use a list of all T1 stats keys for initialization
        team1_total_stats = {k: 0 for k in STAT_KEYS_T1}
        
        # Sum player-recorded stats
        for player in game_data['roster']['Team1']:
            player_stats = game_data['player_stats'].get(player['name'], {})
            
            for key in team1_total_stats:
                team1_total_stats[key] += player_stats.get(key, 0)
                    
        # Add Team Rebounds (which were excluded from player totals)
        team1_total_stats['Off_Rebounds'] += game_data['team1_team_rebounds']['Off_Rebounds']
        team1_total_stats['Def_Rebounds'] += game_data['team1_team_rebounds']['Def_Rebounds']
        
        return team1_total_stats
        
    elif team_name == 'Team2':
        return game_data['team2_generic_stats']
        
    return {} 

def get_roster(team_name):
    """Retrieves the roster for a specified team."""
    return game_data['roster'].get(team_name, [])

# --- INITIALIZATION ---
load_data()