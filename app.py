from flask import Flask, render_template
import pandas as pd


app = Flask(__name__)

# Rank System Configuration in Python
rank_config = [
    {'name': 'Bronze 3', 'emoji': '🥉', 'min_points': 0},
    {'name': 'Bronze 2', 'emoji': '🥉', 'min_points': 150},
    {'name': 'Bronze 1', 'emoji': '🥉', 'min_points': 300},
    {'name': 'Silver 3', 'emoji': '🥈', 'min_points': 450},
    {'name': 'Silver 2', 'emoji': '🥈', 'min_points': 600},
    {'name': 'Silver 1', 'emoji': '🥈', 'min_points': 750},
    {'name': 'Gold 3', 'emoji': '🥇', 'min_points': 900},
    {'name': 'Gold 2', 'emoji': '🥇', 'min_points': 1050},
    {'name': 'Gold 1', 'emoji': '🥇', 'min_points': 1200},
    {'name': 'Platinum 3', 'emoji': '🏆', 'min_points': 1350},
    {'name': 'Platinum 2', 'emoji': '🏆', 'min_points': 1500},
    {'name': 'Platinum 1', 'emoji': '🏆', 'min_points': 1650},
    {'name': 'Diamond 3', 'emoji': '💎', 'min_points': 1800},
    {'name': 'Diamond 2', 'emoji': '💎', 'min_points': 1950},
    {'name': 'Diamond 1', 'emoji': '💎', 'min_points': 2100},
    {'name': 'Master 3', 'emoji': '🔥', 'min_points': 2250},
    {'name': 'Master 2', 'emoji': '🔥', 'min_points': 2400},
    {'name': 'Master 1', 'emoji': '🔥', 'min_points': 2550},
    {'name': 'Grandmaster 3', 'emoji': '🚀', 'min_points': 2700},
    {'name': 'Grandmaster 2', 'emoji': '🚀', 'min_points': 2850},
    {'name': 'Grandmaster 1', 'emoji': '🚀', 'min_points': 3000},
    {'name': 'Challenger', 'emoji': '🌟', 'min_points': 3150},
]




# Dynamically add Master Prestige levels
for i in range(2, 101):
    rank_config.append({
        'name': f'Master Prestige {i}',
        'emoji': '⭐',
        'min_hours': 105 + (i - 1) * 5  # Each level requires 5 additional hours
    })

# Achievement Configuration
# Achievement Configuration
achievement_config = {
    'distance_badges': [
        {'name': '100 km', 'emoji': '💯', 'threshold': 100, 'count': 0},
        {'name': '200 km', 'emoji': '🔱', 'threshold': 200, 'count': 0},
        {'name': '300 km', 'emoji': '⚜️', 'threshold': 300, 'count': 0},
    ],
    'duration_badges': [
        {'name': '3 Hours', 'emoji': '⌛', 'threshold': 3, 'count': 0},
        {'name': '6 Hours', 'emoji': '⏱️', 'threshold': 6, 'count': 0},
        {'name': '12 Hours', 'emoji': '🌇', 'threshold': 12, 'count': 0},
    ],
    'special_occasions': [
        {'name': 'New Year Run', 'emoji': '🎉', 'dates': ['01-01'], 'count': 0},
        {'name': 'Christmas Run', 'emoji': '🎄', 'dates': ['12-25'], 'count': 0},
    ],
    'additional_achievements': [
        {
            'name': 'Marathon Master',
            'emoji': '4️⃣2️⃣🏃',
            'description': 'Completed a marathon (42.195 km)',
            'count': 0,
            'type': 'Run',
            'distance': 42195
        },
        {
            'name': 'Half Marathon Master',
            'emoji': '️2️⃣1️⃣🏃',
            'description': 'Completed a half marathon (21.0975 km)',
            'count': 0,
            'type': 'Run',
            'distance': 21097.5
        },
    ]
}

# Load and preprocess the CSV data
def load_data():
    # Adjust the file path if necessary
    df = pd.read_csv('activities.csv')

    # Convert necessary columns to numeric, handling errors
    numeric_columns = ['Calories', 'Distance', 'Elapsed Time', 'Average Speed', 'Elevation Gain', 'Max Heart Rate', 'Average Heart Rate']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert dates to datetime objects
    df['Activity Date'] = pd.to_datetime(df['Activity Date'], errors='coerce')

    return df

# Calculate summary statistics
def calculate_stats(df):
    stats = {
        'total_calories': df['Calories'].sum(),
        'total_distance': df['Distance'].sum(),  # Assuming distance is in meters
        'total_time': df['Elapsed Time'].sum(),  # Assuming time is in seconds
        'average_speed': df['Average Speed'].mean(),
        'activity_count': df.shape[0],
    }
    return stats

def get_user_rank(total_hours, rank_config):
    # Iterate over rank_config in reverse to find the highest rank the user qualifies for
    for rank in reversed(rank_config):
        if total_hours >= rank['min_hours']:
            return rank
    # If no rank is found, return the lowest rank
    return rank_config[0]

def calculate_coins(df):
    # Constants
    EVEREST_HEIGHT = 8848  # in meters
    PIZZA_CALORIES = 1000  # kcal
    HEARTBEAT_UNIT = 150  # heartbeats per coin

    # Ensure necessary columns are numeric
    df['Total Elevation Gain'] = pd.to_numeric(df['Elevation Gain'], errors='coerce').fillna(0)
    df['Max Heart Rate'] = pd.to_numeric(df['Max Heart Rate'], errors='coerce').fillna(0)
    df['Average Heart Rate'] = pd.to_numeric(df['Average Heart Rate'], errors='coerce').fillna(0)

    # Estimate total heartbeats if average heart rate is available
    df['Total Heartbeats'] = df['Average Heart Rate'] * (df['Elapsed Time'] / 60)

    total_elevation_gain = df['Total Elevation Gain'].sum()
    total_calories = df['Calories'].sum()
    total_heartbeats = df['Total Heartbeats'].sum()

    # Calculate coins
    everest_coins = total_elevation_gain / EVEREST_HEIGHT
    pizza_coins = total_calories / PIZZA_CALORIES
    heartbeat_coins = total_heartbeats / HEARTBEAT_UNIT

    coins = {
        'everest_coins': everest_coins,
        'pizza_coins': pizza_coins,
        'heartbeat_coins': heartbeat_coins
    }

    return coins

def calculate_achievements(df, achievement_config):
    achievements = []

    # Distance Badges
    total_distance_km = df['Distance'].sum() / 1000
    for badge in achievement_config['distance_badges']:
        badge_count = int(total_distance_km // badge['threshold'])
        if badge_count > 0:
            achievements.append({
                'name': badge['name'],
                'emoji': badge['emoji'],
                'count': badge_count
            })

    # Duration Badges
    total_hours = df['Elapsed Time'].sum() / 3600
    for badge in achievement_config['duration_badges']:
        badge_count = int(total_hours // badge['threshold'])
        if badge_count > 0:
            achievements.append({
                'name': badge['name'],
                'emoji': badge['emoji'],
                'count': badge_count
            })

    # Marathon and Half Marathon
    for achievement in achievement_config['additional_achievements']:
        completed_activities = df[(df['Activity Type'] == achievement['type']) & (df['Distance'] >= achievement['distance'])]
        achievement_count = len(completed_activities)
        if achievement_count > 0:
            achievements.append({
                'name': achievement['name'],
                'emoji': achievement['emoji'],
                'count': achievement_count
            })

    # Special Occasions
    df['Activity Date String'] = df['Activity Date'].dt.strftime('%m-%d')
    for occasion in achievement_config['special_occasions']:
        occasion_activities = df[df['Activity Date String'].isin(occasion['dates'])]
        occasion_count = len(occasion_activities)
        if occasion_count > 0:
            achievements.append({
                'name': occasion['name'],
                'emoji': occasion['emoji'],
                'count': occasion_count
            })

    return achievements



def filter_activities_by_timeframe(df, timeframe):
    now = pd.Timestamp.now()
    if timeframe == 'weekly':
        start_date = now - pd.Timedelta(days=7)
    elif timeframe == 'last6months':
        start_date = now - pd.DateOffset(months=6)
    elif timeframe == 'lastyear':
        start_date = now - pd.DateOffset(years=1)
    else:
        return df  # All time

    filtered_df = df[df['Activity Date'] >= start_date]
    return filtered_df

# Load data once when the server starts
dataframe = load_data()
stats = calculate_stats(dataframe)
total_hours = stats['total_time'] / 3600
user_rank = get_user_rank(total_hours, rank_config)
coins = calculate_coins(dataframe)
achievements = calculate_achievements(dataframe, achievement_config)

@app.route('/')
def index():
    return render_template('index.html', stats=stats, user_rank=user_rank, total_hours=total_hours, coins=coins, achievements=achievements)

if __name__ == '__main__':
    app.run(debug=True)
