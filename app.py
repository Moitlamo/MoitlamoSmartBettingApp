import streamlit as st
import requests
import itertools

# Set up the webpage layout
st.set_page_config(page_title="Global Bet Grouper", layout="wide")

st.title("MoitlamoGlobal Smart Bet Grouper & Auto-Picker")
st.write("Pull live odds from any continent, let the algorithm find value, and group them for an edge.")

# ==========================================
# SECTION 1: SIDEBAR (API & BANKROLL)
# ==========================================
st.sidebar.header("1. Settings & Bankroll")
api_key = st.sidebar.text_input("The Odds API Key", type="password", help="Paste your key from the-odds-api.com")
unit_stake = st.sidebar.number_input("Unit Stake (BWP) per line", min_value=1.0, value=10.0, step=1.0)

# Initialize a Bet Slip in the app's memory if it doesn't exist yet
if "bet_slip" not in st.session_state:
    st.session_state.bet_slip = []

# ==========================================
# SECTION 2: GLOBAL MATCH SELECTION
# ==========================================
st.subheader("2. Select Your Global Matches")

# A dictionary organizing leagues by continent
regions = {
    "Europe": {
        "England - Premier League": "soccer_epl",
        "England - Championship": "soccer_efl_champ",
        "Spain - La Liga": "soccer_spain_la_liga",
        "Italy - Serie A": "soccer_italy_serie_a",
        "Germany - Bundesliga": "soccer_germany_bundesliga",
        "France - Ligue 1": "soccer_france_ligue_1",
        "Netherlands - Eredivisie": "soccer_netherlands_eredivisie",
        "Portugal - Primeira Liga": "soccer_portugal_primeira_liga",
        "UEFA Champions League": "soccer_uefa_champs_league",
        "UEFA Europa League": "soccer_uefa_europa_league"
    },
    "Asia & Middle East": {
        "Saudi Arabia - Pro League": "soccer_saudi_arabia_pro_league",
        "Japan - J League": "soccer_japan_j_league",
        "South Korea - K League 1": "soccer_korea_kleague1",
        "China - Super League": "soccer_china_superleague",
        "Australia - A-League": "soccer_australia_aleague",
        "AFC Champions League": "soccer_afc_champs_league"
    },
    "Africa": {
        "South Africa - Premier Division": "soccer_south_africa_premier_league",
        "CAF Champions League": "soccer_caf_champs_league",
        "Africa Cup of Nations": "soccer_africa_cup_of_nations"
    },
    "Americas": {
        "USA - Major League Soccer": "soccer_usa_mls",
        "Brazil - Serie A": "soccer_brazil_campeonato",
        "Brazil - Serie B": "soccer_brazil_serie_b",
        "Argentina - Liga Profesional": "soccer_argentina_primera_division",
        "Mexico - Liga MX": "soccer_mexico_ligamx",
        "Copa Libertadores": "soccer_conmebol_libertadores"
    }
}

# Cascading Dropdowns
col_region, col_league = st.columns(2)

with col_region:
    selected_region = st.selectbox("Step 1: Choose a Continent:", list(regions.keys()))

with col_league:
    selected_league_name = st.selectbox("Step 2: Choose the League:", list(regions[selected_region].keys()))

selected_league_key = regions[selected_region][selected_league_name]

# Fetch Button
if st.button("Fetch Live Matches"):
    if not api_key:
        st.warning("Please enter your Odds API Key in the sidebar first!")
    else:
        with st.spinner(f"Fetching live odds for {selected_league_name}..."):
            url = f"https://api.the-odds-api.com/v4/sports/{selected_league_key}/odds"
            params = {
                "apiKey": api_key,
                "regions": "uk,eu",
                "markets": "h2h",
                "oddsFormat": "decimal"
            }
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if not data:
                    st.info("No upcoming matches found for this league right now. (They might be out of season!)")
                else:
                    st.session_state.live_matches = data
            else:
                st.error("Error fetching data. Check your API Key or try a different league.")

# Display the matches and create manual buttons to add them to the slip
if "live_matches" in st.session_state and st.session_state.live_matches:
    st.write(f"**Live Market Odds for {selected_league_name}**")
    
    for match in st.session_state.live_matches:
        match_title = f"{match['home_team']} vs {match['away_team']}"
        
        if match['bookmakers']:
            outcomes = match['bookmakers'][0]['markets'][0]['outcomes']
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            col1.write(f"Match: {match_title}")
            
            # Create a clickable button for Home, Draw, and Away odds
            for idx, outcome in enumerate(outcomes):
                btn_col = [col2, col3, col4][idx]
                btn_label = f"{outcome['name']} ({outcome['price']})"
                
                if btn_col.button(btn_label, key=f"{match['id']}_{outcome['name']}"):
                    st.session_state.bet_slip.append({
                        "match": match_title,
                        "selection": outcome['name'],
                        "odds": float(outcome['price'])
                    })
        st.write("---")

# ==========================================
# SECTION 3: AI AUTO-SLIP GENERATOR
# ==========================================
st.subheader("Auto-Generate Smart Slip")
st.write("Let the algorithm scan the market and pick the highest mathematical probabilities for you.")

if "live_matches" in st.session_state and st.session_state.live_matches:
    col_auto1, col_auto2 = st.columns([1, 2])
    
    with col_auto1:
        auto_size = st.number_input("How many matches to pick?", min_value=2, max_value=6, value=3)
        
    with col_auto2:
        st.write("") # Spacing alignment
        st.write("")
        if st.button("Generate Value Slip"):
            auto_picks = []
            
            # Scan every live match currently loaded
            for match in st.session_state.live_matches:
                if match['bookmakers']:
                    outcomes = match['bookmakers'][0]['markets'][0]['outcomes']
                    
                    # Find the outcome with the lowest decimal odds
                    safest_outcome = min(outcomes, key=lambda x: float(x['price']))
                    
                    # Filter for the "Banker Sweet Spot" (Odds between 1.30 and 1.80)
                    if 1.30 <= float(safest_outcome['price']) <= 1.80:
                        auto_picks.append({
                            "match": f"{match['home_team']} vs {match['away_team']}",
                            "selection": safest_outcome['name'],
                            "odds": float(safest_outcome['price'])
                        })
            
            # Sort the best picks from safest (lowest odds) to riskiest
            auto_picks = sorted(auto_picks, key=lambda x: x['odds'])
            
            # Take exactly the number of matches the user asked for
            final_picks = auto_picks[:int(auto_size)]
            
            if len(final_picks) < auto_size:
                st.warning(f"Market check: Only found {len(final_picks)} matches meeting the value criteria right now. Try checking a different league!")
            else:
                st.session_state.bet_slip = final_picks
                st.success(f"Successfully loaded {len(final_picks)} high-probability 'Bankers' into your slip!")
                st.rerun() # Instantly refresh the app to show the new slip
else:
    st.info("Fetch some live matches first so the algorithm has data to analyze.")

st.divider()

# ==========================================
# SECTION 4: THE SMART BET SLIP & SYSTEM MATH
# ==========================================
st.subheader("3. Your Smart Bet Slip")

if not st.session_state.bet_slip:
    st.info("Your slip is empty. Click odds above to add matches.")
else:
    # Loop through the bet slip to display picks, probabilities, and the Remove button
    for idx, item in enumerate(st.session_state.bet_slip):
        col_info, col_btn = st.columns([4, 1])
        
        with col_info:
            implied_prob = (1 / item['odds']) * 100
            st.write(f"-> {item['match']} | Pick: {item['selection']} | Odds: {item['odds']} (Implied: {implied_prob:.1f}%)")
            
        with col_btn:
            # The Remove Button logic
            if st.button("Remove", key=f"remove_{idx}"):
                st.session_state.bet_slip.pop(idx)
                st.rerun() # Instantly refresh the app
                
    if st.button("Clear Entire Slip"):
        st.session_state.bet_slip = []
        st.rerun()

    st.divider()
    
    # SYSTEM BET CALCULATOR
    st.subheader("4. System Bet Analysis")
    total_selections = len(st.session_state.bet_slip)
    
    if total_selections >= 2:
        parlay_size = st.slider("Group by (e.g., 2 for Doubles, 3 for Trebles)", min_value=2, max_value=total_selections, value=2)
        
        # Calculate permutations using itertools
        combinations = list(itertools.combinations(st.session_state.bet_slip, parlay_size))
        total_lines = len(combinations)
        total_cost = total_lines * unit_stake
        
        max_payout = 0
        for combo in combinations:
            combined_odds = 1.0
            for leg in combo:
                combined_odds *= leg['odds']
            max_payout += (combined_odds * unit_stake)
            
        st.success(f"System Mode: Round Robin By {parlay_size}s")
        
        # Display Financials
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Total Combinations (Lines)", total_lines)
        col_b.metric("Total Cost", f"{total_cost:.2f} BWP")
        col_c.metric("Max Potential Payout", f"{max_payout:.2f} BWP")
    else:
        st.warning("You need at least 2 matches in your slip to build a system.")