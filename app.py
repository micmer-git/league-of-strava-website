from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

# Rank System Configuration in Python (Based on Total Hours)
rank_config = [
    {'name': 'Bronze 3', 'emoji': '🥉', 'min_hours': 0},
    {'name': 'Bronze 2', 'emoji': '🥉', 'min_hours': 5},
    {'name': 'Bronze 1', 'emoji': '🥉', 'min_hours': 10},
    {'name': 'Silver 3', 'emoji': '🥈', 'min_hours': 15},
    {'name': 'Silver 2', 'emoji': '🥈', 'min_hours': 20},
    {'name': 'Silver 1', 'emoji': '🥈', 'min_hours': 25},
    {'name': 'Gold 3', 'emoji': '🥇', 'min_hours': 30},
    {'name': 'Gold 2', 'emoji': '🥇', 'min_hours': 35},
    {'name': 'Gold 1', 'emoji': '🥇', 'min_hours': 40},
    {'name': 'Platinum 3', 'emoji': '🏆', 'min_hours': 45},
    {'name': 'Platinum 2', 'emoji': '🏆', 'min_hours': 50},
    {'name': 'Platinum 1', 'emoji': '🏆', 'min_hours': 55},
    {'name': 'Diamond 3', 'emoji': '💎', 'min_hours': 60},
    {'name': 'Diamond 2', 'emoji': '💎', 'min_hours': 65},
    {'name': 'Diamond 1', 'emoji': '💎', 'min_hours': 70},
    {'name': 'Master 3', 'emoji': '🔥', 'min_hours': 75},
    {'name': 'Master 2', 'emoji': '🔥', 'min_hours': 80},
    {'name': 'Master 1', 'emoji': '🔥', 'min_hours': 85},
    {'name': 'Grandmaster 3', 'emoji': '🚀', 'min_hours': 90},
    {'name': 'Grandmaster 2', 'emoji': '🚀', 'min_hours': 95},
    {'name': 'Grandmaster 1', 'emoji': '🚀', 'min_hours': 100},
    {'name': 'Challenger', 'emoji': '🌟', 'min_hours': 105},
]

# Dynamically add Master Prestige levels
for i in range(2, 101):
    rank_config.append({
        'name': f'Master Prestige {i}',
        'emoji': '⭐',
        'min_hours': 105 + (i - 1) * 5  # Each level requires 5 additional hours
    })

# Achievement Configuration
achievement_config = {
    'distance_badges': [
        {'name': '100 km', 'emoji': '💯', 'threshold': 100, 'count': 0},
        {'name': '200 km', 'emoji': '🔱', 'threshold': 200, 'count': 0},
        {'name': '300 km', 'emoji': '⚜️', 'threshold': 300, 'count': 0},
    ],
    'duration_badges': [
        {'name': '3 Hours', 'emoji': '⌛', 'threshold': 3, 'count': 0},  # threshold in hours
        {'name': '6 Hours', 'emoji': '⏱️', 'threshold': 6, 'count': 0},
        {'name': '12 Hours', 'emoji': '🌇', 'threshold': 12, 'count': 0},
    ],
    'special_occasions': [
        {'name': 'New Year Run', 'emoji': '🎉', 'dates': ['01-01'], 'count': 0},
        {'name': 'Christmas Run', 'emoji': '🎄', 'dates': ['12-25'], 'count': 0},
        # Add more special occasions as needed
    ],
    'additional_achievements': [
        {
            'name': 'Marathon Master',
            'emoji': '4️⃣2️⃣🏃',
            'description': 'Completed a marathon (42.195 km)',
            'count': 0,
            'type': 'Run',  # Specify the activity type
            'distance': 42195  # Marathon distance in meters
        },
        {
            'name': 'Half Marathon Master',
            'emoji': '️2️⃣1️⃣🏃',
            'description': 'Completed a half marathon (21.0975 km)',
            'count': 0,
            'type': 'Run',  # Specify the activity type
            'distance': 21097.5  # Half marathon distance in meters
        },
        # Add other achievements as needed
    ]
}

# Load and preprocess the CSV data
def load_data():
    # Adjust the file path if necessary
    df = pd.read_csv('activities.csv')

    # Convert necessary columns to numeric, handling errors
    numeric_columns = ['Calories', 'Distance', 'Elapsed Time', 'Elevation Gain', 'Max Heart Rate', 'Average Heart Rate']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert dates to datetime objects
    df['Activity Date'] = pd.to_datetime(df['Activity Date'], errors='coerce')

    return df

def get_time_filtered_df(df, period):
    now = pd.Timestamp.now()
    if period == 'lifetime':
        return df
    elif period == 'last_year':
        start_date = now - pd.DateOffset(years=1)
    elif period == 'ytd':
        start_date = pd.Timestamp(year=now.year, month=1, day=1)
    elif period == 'last_30_days':
        start_date = now - pd.Timedelta(days=30)
    else:
        return df  # Default to lifetime
    filtered_df = df[df['Activity Date'] >= start_date]
    return filtered_df

# Calculate summary statistics
def calculate_stats(df):
    stats = {
        'total_calories': df['Calories'].sum(),
        'total_distance': df['Distance'].sum(),  # Assuming distance is in meters
        'total_time': df['Elapsed Time'].sum(),  # Assuming time is in seconds
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

    coins = [
        {'name': 'Everest Coins', 'emoji': '🏔️', 'count': everest_coins},
        {'name': 'Pizza Coins', 'emoji': '🍕', 'count': pizza_coins},
        {'name': 'Heartbeat Coins', 'emoji': '❤️', 'count': heartbeat_coins}
    ]

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

# Load data once when the server starts
dataframe = load_data()

@app.route('/')
def index():
    periods = ['lifetime', 'last_year', 'ytd', 'last_30_days']
    period_names = {
        'lifetime': 'Lifetime',
        'last_year': 'Last Year',
        'ytd': 'Year to Date',
        'last_30_days': 'Last 30 Days'
    }

    achievements_by_period = {}

    for period in periods:
        filtered_df = get_time_filtered_df(dataframe, period)
        achievements = calculate_achievements(filtered_df, achievement_config)
        coins = calculate_coins(filtered_df)
        # Include coins in achievements
        coins_as_achievements = []
        for coin in coins:
            coins_as_achievements.append({
                'name': coin['name'],
                'emoji': coin['emoji'],
                'count': coin['count']
            })
        # Combine achievements and coins
        achievements_by_period[period] = achievements + coins_as_achievements

    # For Rank and Stats, we will use Lifetime data
    stats = calculate_stats(dataframe)
    total_hours = stats['total_time'] / 3600
    user_rank = get_user_rank(total_hours, rank_config)

    return render_template('index.html',
                           user_rank=user_rank,
                           total_hours=total_hours,
                           stats=stats,
                           achievements_by_period=achievements_by_period,
                           period_names=period_names)

if __name__ == '__main__':
    app.run(debug=True)
