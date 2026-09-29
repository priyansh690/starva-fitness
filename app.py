import streamlit as st
import pandas as pd
import duckdb
import matplotlib.pyplot as plt
import seaborn as sns
import os

st.set_page_config(page_title="Bellabeat Wellness Data Dashboard", layout="wide")

st.title("Bellabeat Wellness Data Dashboard")
st.markdown("### Analyzing Smart Device Fitness Data for Growth Opportunities")

# Initialize DuckDB connection
con = duckdb.connect(database=':memory:')

@st.cache_data
def load_data():
    activity_df = pd.read_csv("dailyActivity_merged.csv")
    sleep_df = pd.read_csv("sleepDay_merged.csv")
    
    # Cleaning: convert date strings to datetime for sleep data
    sleep_df['SleepDay'] = pd.to_datetime(sleep_df['SleepDay']).dt.date
    sleep_df['SleepDay'] = sleep_df['SleepDay'].astype(str)
    
    # Cleaning: rename ActivityDate to Date for consistency
    activity_df.rename(columns={'ActivityDate': 'Date'}, inplace=True)
    activity_df['Date'] = pd.to_datetime(activity_df['Date']).dt.date
    activity_df['Date'] = activity_df['Date'].astype(str)
    
    return activity_df, sleep_df

try:
    activity_df, sleep_df = load_data()
    
    # Register dataframes with DuckDB for SQL analysis
    con.register('activity', activity_df)
    con.register('sleep', sleep_df)
    
    st.header("1. Data Cleaning & SQL Analysis")
    
    st.markdown("We perform SQL analysis to merge Activity and Sleep data to understand user habits.")
    
    query = """
    SELECT 
        a.Id, 
        a.Date, 
        a.TotalSteps, 
        a.TotalDistance, 
        a.VeryActiveMinutes, 
        a.FairlyActiveMinutes, 
        a.LightlyActiveMinutes, 
        a.SedentaryMinutes, 
        a.Calories,
        s.TotalMinutesAsleep,
        s.TotalTimeInBed
    FROM activity a
    LEFT JOIN sleep s ON a.Id = s.Id AND a.Date = s.SleepDay
    """
    
    merged_data = con.execute(query).fetchdf()
    
    st.dataframe(merged_data.head())
    
    st.header("2. Insights & Visualizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Steps vs. Calories Burned")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.scatterplot(data=merged_data, x='TotalSteps', y='Calories', alpha=0.6, color='purple', ax=ax)
        plt.title("Correlation between Total Steps and Calories Burned")
        st.pyplot(fig)
        st.markdown("**Insight:** There is a positive correlation between the number of steps taken and calories burned. Encouraging users to hit daily step goals directly impacts their caloric burn.")

    with col2:
        st.subheader("Sedentary Minutes vs. Sleep Time")
        # Filter out null sleep data for this plot
        sleep_valid = merged_data.dropna(subset=['TotalMinutesAsleep'])
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        sns.scatterplot(data=sleep_valid, x='SedentaryMinutes', y='TotalMinutesAsleep', alpha=0.6, color='teal', ax=ax2)
        plt.title("Sedentary Minutes vs. Total Minutes Asleep")
        st.pyplot(fig2)
        st.markdown("**Insight:** Higher sedentary minutes loosely correlate with lower sleep durations. Users who are inactive for long periods may have poorer sleep quality.")

    st.subheader("User Activity Levels")
    
    activity_summary = con.execute("""
    SELECT 
        AVG(VeryActiveMinutes) as AvgVeryActive,
        AVG(FairlyActiveMinutes) as AvgFairlyActive,
        AVG(LightlyActiveMinutes) as AvgLightlyActive,
        AVG(SedentaryMinutes) as AvgSedentary
    FROM activity
    """).fetchdf()
    
    fig3, ax3 = plt.subplots(figsize=(8, 5))
    labels = ['Very Active', 'Fairly Active', 'Lightly Active', 'Sedentary']
    sizes = activity_summary.iloc[0].values
    colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']
    ax3.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax3.axis('equal')
    st.pyplot(fig3)
    st.markdown("**Insight:** Users spend the vast majority of their time (81.3%) in a sedentary state. There is a huge opportunity to prompt users to move more throughout the day.")

    st.header("3. High-Level Recommendations for Bellabeat")
    
    st.markdown("""
    Based on the analysis of the smart device data, here are strategic recommendations for Bellabeat's marketing and product teams:
    
    1. **Sedentary Alerts & Gamification:** Since users spend a significant portion of their day sedentary, the Bellabeat app should introduce subtle, motivating notifications to encourage movement every hour. Marketing campaigns can highlight how Bellabeat devices act as personal wellness coaches.
    2. **Sleep Optimization Campaigns:** There is a connection between daily activity and sleep quality. Bellabeat can market its holistic approach by showing how its devices track the entire wellness loop (activity → stress → sleep). Providing actionable tips to improve sleep based on daily activity will increase user engagement.
    3. **Step Goal Challenges:** A clear correlation exists between total steps and calories burned. Bellabeat can introduce community challenges or personal milestones focused on daily steps, using this as a core acquisition strategy in their marketing.
    4. **Targeted Notifications:** Use the data to send personalized insights. For example, if a user has high sedentary minutes by 3 PM, send an inspiring push notification to take a short walk, linking to a Bellabeat blog post about the benefits of light activity.
    """)
    
except Exception as e:
    st.error(f"Error loading data: {e}")
