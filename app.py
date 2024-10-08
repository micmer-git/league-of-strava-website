from flask import Flask, render_template, request
import pandas as pd
from werkzeug.utils import secure_filename
import logging
import os

app = Flask(__name__)

# Configuration
ALLOWED_EXTENSIONS = {'csv'}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 Megabytes

# Initialize logging
logging.basicConfig(level=logging.INFO)

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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Load and preprocess the CSV data
def process_dataframe(dataframe):
    # Ensure necessary columns are present
    required_columns = ['Calories', 'Distance', 'Elapsed Time', 'Elevation Gain',
                        'Max Heart Rate', 'Average Heart Rate', 'Activity Type', 'Activity Date']
    missing_columns = [col for col in required_columns if col not in dataframe.columns]
    if missing_columns:
        error = f"The following required columns are missing in the uploaded file: {', '.join(missing_columns)}"
        return None, error

    # Convert necessary columns to numeric, handling errors
    numeric_columns = ['Calories', 'Distance', 'Elapsed Time', 'Elevation Gain', 'Max Heart Rate', 'Average Heart Rate']
    for col in numeric_columns:
        dataframe[col] = pd.to_numeric(dataframe[col], errors='coerce')

    # Drop rows with NaN values in numeric columns
    dataframe = dataframe.dropna(subset=numeric_columns).copy()

    # Convert 'Activity Date' to datetime using the correct format
    # Assuming the format is 'Mar 19, 2016, 8:44:35 AM'
    date_format = '%b %d, %Y, %I:%M:%S %p'
    dataframe['Activity Date'] = pd.to_datetime(
        dataframe['Activity Date'], format=date_format, errors='coerce')

    # Check if 'Activity Date' conversion was successful
    if dataframe['Activity Date'].isnull().all():
        error = "All 'Activity Date' values are invalid or could not be parsed. Please check the date format in your CSV file."
        return None, error

    # Drop rows with invalid dates
    dataframe = dataframe.dropna(subset=['Activity Date']).copy()

    # Ensure 'Activity Type' is a string
    dataframe['Activity Type'] = dataframe['Activity Type'].astype(str)

    # Check if DataFrame is empty
    if dataframe.empty:
        error = 'No valid data found after processing. Please check your CSV file.'
        return None, error

    return dataframe, None

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
    df['Calories'] = pd.to_numeric(df['Calories'], errors='coerce').fillna(0)

    # Estimate total heartbeats if average heart rate is available
    df['Total Heartbeats'] = df['Average Heart Rate'] * (df['Elapsed Time'] / 60)

    total_elevation_gain = df['Total Elevation Gain'].sum()
    total_calories = df['Calories'].sum()
    total_heartbeats = df['Total Heartbeats'].sum()

    # Calculate coins
    everest_coins = total_elevation_gain / EVEREST_HEIGHT
    pizza_coins = total_calories / PIZZA_CALORIES
    heartbeat_coins = total_heartbeats / HEARTBEAT_UNIT

    # New coins (optional, can be removed if not needed)
    climber_coin = len(df[df['Total Elevation Gain'] > 1000])
    michelin_star_coin = len(df[df['Calories'] > 2000])

    # Coins collected in the last week
    last_week = pd.Timestamp.now() - pd.Timedelta(days=7)
    coins_last_week = df[df['Activity Date'] >= last_week]
    everest_coins_last_week = coins_last_week['Total Elevation Gain'].sum() / EVEREST_HEIGHT
    pizza_coins_last_week = coins_last_week['Calories'].sum() / PIZZA_CALORIES
    heartbeat_coins_last_week = coins_last_week['Total Heartbeats'].sum() / HEARTBEAT_UNIT

    coins = [
        {'name': 'Everest Coins', 'emoji': '🏔️', 'count': round(everest_coins, 1), 'last_week': round(everest_coins_last_week, 1)},
        {'name': 'Pizza Coins', 'emoji': '🍕', 'count': round(pizza_coins, 1), 'last_week': round(pizza_coins_last_week, 1)},
        {'name': 'Heartbeat Coins', 'emoji': '❤️', 'count': round(heartbeat_coins, 1), 'last_week': round(heartbeat_coins_last_week, 1)},
        {'name': 'Climber Activities', 'emoji': '⛰️', 'count': climber_coin, 'last_week': 0},
        {'name': 'Michelin Star Burner', 'emoji': '🔥', 'count': michelin_star_coin, 'last_week': 0}
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
        completed_activities = df[
            (df['Activity Type'].str.lower() == achievement['type'].lower()) &
            (df['Distance'] >= achievement['distance'])
        ]
        achievement_count = len(completed_activities)
        if achievement_count > 0:
            achievements.append({
                'name': achievement['name'],
                'emoji': achievement['emoji'],
                'count': achievement_count
            })

    return achievements

def calculate_progress(total_hours, rank_config):
    # Find current rank index
    sorted_ranks = sorted(rank_config, key=lambda x: x['min_hours'])
    current_rank = None
    next_rank = None
    for rank in sorted_ranks:
        if total_hours >= rank['min_hours']:
            current_rank = rank
    current_index = sorted_ranks.index(current_rank)
    if current_index < len(sorted_ranks) - 1:
        next_rank = sorted_ranks[current_index + 1]
    else:
        next_rank = current_rank  # No next rank

    if next_rank['min_hours'] > current_rank['min_hours']:
        progress = (total_hours - current_rank['min_hours']) / (next_rank['min_hours'] - current_rank['min_hours']) * 100
    else:
        progress = 100

    return round(progress, 1), next_rank['min_hours'] - current_rank['min_hours']

def calculate_hours_last_week(df):
    last_week = pd.Timestamp.now() - pd.Timedelta(days=7)
    hours_last_week = df[df['Activity Date'] >= last_week]['Elapsed Time'].sum() / 3600
    return round(hours_last_week, 2)

def calculate_hours_total(df):
    total_hours = df['Elapsed Time'].sum() / 3600
    return round(total_hours, 2)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if the POST request has the file part
        if 'file' not in request.files:
            error = 'No file part in the request.'
            return render_template('index.html', error=error)
        file = request.files['file']
        # If the user does not select a file
        if file.filename == '':
            error = 'No file selected.'
            return render_template('index.html', error=error)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Optionally, save the file to a temporary location
            # file.save(os.path.join('uploads', filename))
            try:
                dataframe = pd.read_csv(file)
                dataframe, error = process_dataframe(dataframe)
                if error:
                    return render_template('index.html', error=error)

                # Proceed with processing
                achievements = calculate_achievements(dataframe, achievement_config)
                coins = calculate_coins(dataframe)
                stats = calculate_stats(dataframe)
                total_hours = calculate_hours_total(dataframe)
                hours_last_week = calculate_hours_last_week(dataframe)
                user_rank = get_user_rank(total_hours, rank_config)
                progress, hours_next_level = calculate_progress(total_hours, rank_config)

                # Now render the dashboard template
                return render_template('dashboard.html',
                                       user_rank=user_rank,
                                       total_hours=total_hours,
                                       stats=stats,
                                       achievements=achievements,
                                       coins=coins,
                                       progress=progress,
                                       hours_next_level=hours_next_level,
                                       hours_last_week=hours_last_week)
            except Exception as e:
                logging.exception("Error processing the file.")
                error = f'An error occurred during processing: {e}'
                return render_template('index.html', error=error)
        else:
            error = 'Invalid file type. Please upload a CSV file.'
            return render_template('index.html', error=error)
    else:
        # GET request, show the file upload form
        return render_template('index.html')

if __name__ == '__main__':
    # Ensure the 'uploads' directory exists if you plan to save files
    # os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
