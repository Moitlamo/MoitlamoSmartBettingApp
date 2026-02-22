import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="Bankroll Simulator", layout="wide")

st.title("Monte Carlo Bankroll Simulator")
st.write("Test your mathematical edge. See if your system survives 1,000 bets.")

st.sidebar.header("Strategy Settings")
starting_bankroll = st.sidebar.number_input("Starting Bankroll (BWP)", value=1000, step=100)
unit_size = st.sidebar.number_input("Unit Size per Bet (BWP)", value=10, step=1)
average_odds = st.sidebar.number_input("Average Decimal Odds (e.g., 1.50)", value=1.50, step=0.05)

st.sidebar.divider()
st.sidebar.header("The Reality Check")
true_win_rate = st.sidebar.slider("Your True Win Rate (%)", min_value=1, max_value=100, value=70)
num_bets = st.sidebar.slider("Number of Bets to Simulate", min_value=100, max_value=5000, value=1000)
num_simulations = st.sidebar.slider("Alternate Realities (Simulations)", min_value=1, max_value=20, value=5)

if st.button("Run Simulation"):
    with st.spinner("Calculating alternate realities..."):
        # Convert win rate percentage to a decimal for math
        win_prob = true_win_rate / 100.0
        
        # Create a blank dataframe to hold the graph data
        sim_data = pd.DataFrame()

        # Run the loop for however many alternate realities you want
        for i in range(num_simulations):
            bankroll_history = [starting_bankroll]
            current_bankroll = starting_bankroll

            # Generate random numbers between 0.0 and 1.0 for every single bet
            random_outcomes = np.random.rand(num_bets)

            for outcome in random_outcomes:
                # If the random number is less than your win rate, you win the bet!
                if outcome <= win_prob:
                    profit = unit_size * (average_odds - 1.0)
                    current_bankroll += profit
                else:
                    # You lost the bet
                    current_bankroll -= unit_size

                # Bankrupt check - if you hit 0, the simulation stops for this timeline
                if current_bankroll <= 0:
                    current_bankroll = 0
                    bankroll_history.append(current_bankroll)
                    break

                bankroll_history.append(current_bankroll)

            # If you went bankrupt early, pad the rest of the timeline with 0s
            while len(bankroll_history) <= num_bets:
                bankroll_history.append(0)

            # Add this specific timeline to the graph data
            sim_data[f"Reality {i+1}"] = bankroll_history

        # Display the results
        st.subheader("Your Bankroll Trajectory")
        st.line_chart(sim_data)
        
        st.success("Simulation Complete! Look at the variance in the graph above.")
        
        st.info("How to read this graph: Each colored line represents a different 'alternate reality' of your betting system. Notice how even with the exact same win rate and odds, short-term luck causes the lines to zigzag differently. If all lines trend upwards, you have a proven mathematical edge.")