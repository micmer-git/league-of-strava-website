from flask import Flask, render_template, request
import pandas as pd
from werkzeug.utils import secure_filename
import logging

app = Flask(__name__)

# Configuration
ALLOWED_EXTENSIONS = {'csv'}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 Megabytes

# Initialize logging
logging.basicConfig(level=logging.INFO)

# [Rank configuration and achievement configuration remain unchanged]

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Rank System Configuration in Python (Based on Total Hours)
rank_config = [
    {'name': 'Bronze 3', 'emoji': '🥉', 'min_hours': 0},
    {'name': 'Bronze 2', 'emoji': '🥉', 'min_hours': 50},
    {'name': 'Bronze 1', 'emoji': '🥉', 'min_hours': 100},
    {'name': 'Silver 3', 'emoji': '🥈', 'min_hours': 150},
    {'name': 'Silver 2', 'emoji': '🥈', 'min_hours': 200},
    {'name': 'Silver 1', 'emoji': '🥈', 'min_hours': 250},
    {'name': 'Gold 3', 'emoji': '🥇', 'min_hours': 300},
    {'name': 'Gold 2', 'emoji': '🥇', 'min_hours': 350},
    {'name': 'Gold 1', 'emoji': '🥇', 'min_hours': 400},
    {'name': 'Platinum 3', 'emoji': '🏆', 'min_hours': 450},
    {'name': 'Platinum 2', 'emoji': '🏆', 'min_hours': 500},
    {'name': 'Platinum 1', 'emoji': '🏆', 'min_hours': 550},
    {'name': 'Diamond 3', 'emoji': '💎', 'min_hours': 600},
    {'name': 'Diamond 2', 'emoji': '💎', 'min_hours': 650},
    {'name': 'Diamond 1', 'emoji': '💎', 'min_hours': 700},
    {'name': 'Master 3', 'emoji': '🔥', 'min_hours': 750},
    {'name': 'Master 2', 'emoji': '🔥', 'min_hours': 800},
    {'name': 'Master 1', 'emoji': '🔥', 'min_hours': 850},
    {'name': 'Grandmaster 3', 'emoji': '🚀', 'min_hours': 900},
    {'name': 'Grandmaster 2', 'emoji': '🚀', 'min_hours': 950},
    {'name': 'Grandmaster 1', 'emoji': '🚀', 'min_hours': 1000},
    {'name': 'Challenger', 'emoji': '🌟', 'min_hours': 1050},
]

# Dynamically add Master Prestige levels
for i in range(2, 101):
    rank_config.append({
        'name': f'Master Prestige {i}',
        'emoji': '⭐',
        'min_hours': 1050 + (i - 1) * 100  # Each level requires 5 additional hours
    })

# Achievement Configuration
# Achievement Configuration
achievement_config = {
    'special_occasions': [
        {'name': 'New Year Run', 'emoji': '🎉', 'dates': ['01-01'], 'category': 'Special Days'},
        {'name': 'Christmas Run', 'emoji': '🎄', 'dates': ['12-25'], 'category': 'Special Days'},
        # Add more special occasions as needed
    ],
    'races': [
        {
            'name': 'Marathon Master',
            'emoji': '4️⃣2️⃣🏃',
            'description': 'Completed a marathon (42.195 km)',
            'type': 'Run',
            'distance': 42.195,  # in meters
            'category': 'Races'
        },
        {
            'name': 'Half Marathon Master',
            'emoji': '️2️⃣1️⃣🏃',
            'description': 'Completed a half marathon (21.0975 km)',
            'type': 'Run',
            'distance': 21.0975,  # in meters
            'category': 'Races'
        },
        # Add other races as needed
    ],
    'triathlon_achievements': [
        {
            'name': 'Sprint Triathlon',
            'emoji': '🏊‍♂️🚴‍♂️🏃‍♂️',
            'description': 'Completed a Sprint Triathlon',
            'distances': {'Swim': 0.750, 'Ride': 20.000, 'Run': 5.000},
            'category': 'Races'
        },
        {
            'name': 'Olympic Triathlon',
            'emoji': '🏊‍♂️🚴‍♂️🏃‍♂️',
            'description': 'Completed an Olympic Triathlon',
            'distances': {'Swim': 1.500, 'Ride': 40.000, 'Run': 10.000},
            'category': 'Races'
        },
        {
            'name': 'Half Ironman',
            'emoji': '🏊‍♂️🚴‍♂️🏃‍♂️',
            'description': 'Completed a Half Ironman',
            'distances': {'Swim': 1.900, 'Ride': 90.000, 'Run': 21.100},
            'category': 'Races'
        },
        {
            'name': 'Ironman',
            'emoji': '🏊‍♂️🚴‍♂️🏃‍♂️',
            'description': 'Completed an Ironman',
            'distances': {'Swim': 3.800, 'Ride': 180.000, 'Run': 42.200},
            'category': 'Races'
        }
    ]
}

# Load and preprocess the CSV data
def load_data():
    # Adjust the file path if necessary
    df = pd.read_csv('activities.csv')

    # Convert necessary columns to numeric, handling errors
    numeric_columns = ['Calories', 'Distance', 'Elapsed Time', 'Elevation Gain', 'Average Heart Rate']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert dates to datetime objects
    df['Activity Date'] = pd.to_datetime(df['Activity Date'], errors='coerce')

    return df

def get_time_filtered_df(df, period):
    now = pd.Timestamp.now()
    if period == 'lifetime':
        return df.copy()
    elif period == 'last_365_days':
        start_date = now - pd.Timedelta(days=365)
    elif period == 'ytd':
        start_date = pd.Timestamp(year=now.year, month=1, day=1)
    elif period == 'last_30_days':
        start_date = now - pd.Timedelta(days=30)
    else:
        return df.copy()  # Default to lifetime
    filtered_df = df[df['Activity Date'] >= start_date].copy()
    return filtered_df

# Calculate summary statistics
def calculate_stats(df):
    stats = {
        'total_calories': df['Calories'].sum(),
        'total_distance': df['Distance'].sum()*1000,  # Assuming distance is in meters
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
    HEARTBEAT_UNIT = 1  # heartbeats per coin

    # Ensure necessary columns are numeric
    df['Total Elevation Gain'] = df['Elevation Gain'].fillna(0)
    df['Average Heart Rate'] = df['Average Heart Rate'].fillna(0)
    df['Calories'] = df['Calories'].fillna(0)

    # Estimate total heartbeats if average heart rate is available
    df['Total Heartbeats'] = df['Average Heart Rate'] * (df['Elapsed Time'] / 60)

    total_elevation_gain = df['Total Elevation Gain'].sum()
    total_calories = df['Calories'].sum()
    total_heartbeats = df['Total Heartbeats'].sum()
    total_hours = df['Elapsed Time'].sum() / 3600
    total_distance_km = df['Distance'].sum() / 1000

    # Calculate coins
    everest_coins = total_elevation_gain / EVEREST_HEIGHT
    pizza_coins = total_calories / PIZZA_CALORIES
    heartbeat_coins = total_heartbeats / HEARTBEAT_UNIT

    # Consistency Coins
    # Weeks with 7 days active
    df['Week'] = df['Activity Date'].dt.isocalendar().week
    df['Year'] = df['Activity Date'].dt.year
    df['Year-Week'] = df['Year'].astype(str) + '-' + df['Week'].astype(str)
    weeks_active = df.groupby('Year-Week')['Activity Date'].nunique()
    weeks_with_7_days = weeks_active[weeks_active >= 7].count()

    # Months with activities
    df['Month'] = df['Activity Date'].dt.to_period('M')
    months_active = df['Month'].nunique()

    # Years with activities
    years_active = df['Year'].nunique()

    coins = [
        {'name': 'Everest Coins', 'emoji': '🏔️', 'count': everest_coins},
        {'name': 'Pizza Coins', 'emoji': '🍕', 'count': pizza_coins},
        {'name': 'Heartbeat Coins', 'emoji': '❤️', 'count': total_heartbeats},
        {'name': 'Total Hours', 'emoji': '⏱️', 'count': total_hours},
        {'name': 'Total Distance', 'emoji': '🚴', 'count': total_distance_km},
        {'name': 'Consistency Coins', 'emoji': '📆', 'count': weeks_with_7_days},
        {'name': 'Months Active', 'emoji': '🗓️', 'count': months_active},
        {'name': 'Years Active', 'emoji': '📅', 'count': years_active}
    ]

    return coins

def calculate_achievements(df, achievement_config):
    achievements = []
    # Ensure 'Distance' is numeric
    df['Distance'] = pd.to_numeric(df['Distance'], errors='coerce')
    df = df.dropna(subset=['Distance'])

    # Races Achievements
    for race in achievement_config.get('races', []):
        completed_activities = df[(df['Activity Type'] == race['type']) & (df['Distance'] >= race['distance'])]
        achievement_count = len(completed_activities)
        if achievement_count > 0:
            achievements.append({
                'name': race['name'],
                'emoji': race['emoji'],
                'count': achievement_count,
                'category': race.get('category', 'Races')
            })

    # Special Occasions
    df['Activity Date String'] = df['Activity Date'].dt.strftime('%m-%d')
    for occasion in achievement_config.get('special_occasions', []):
        occasion_activities = df[df['Activity Date String'].isin(occasion['dates'])]
        occasion_count = len(occasion_activities)
        if occasion_count > 0:
            achievements.append({
                'name': occasion['name'],
                'emoji': occasion['emoji'],
                'count': occasion_count,
                'category': occasion.get('category', 'Special Days')
            })

    # Triathlon Achievements
    df['Date'] = df['Activity Date'].dt.date
    dates = df['Date'].unique()
    for triathlon in achievement_config.get('triathlon_achievements', []):
        count = 0
        for date in dates:
            day_activities = df[df['Date'] == date]
            # Check for Swim, Ride, Run
            swim_distance = day_activities[day_activities['Activity Type'] == 'Swim']['Distance'].sum()
            ride_distance = day_activities[day_activities['Activity Type'] == 'Ride']['Distance'].sum()
            run_distance = day_activities[day_activities['Activity Type'] == 'Run']['Distance'].sum()
            distances = triathlon['distances']
            if (swim_distance >= distances.get('Swim', 0) and
                ride_distance >= distances.get('Ride', 0) and
                run_distance >= distances.get('Run', 0)):
                count += 1
        if count > 0:
            achievements.append({
                'name': triathlon['name'],
                'emoji': triathlon['emoji'],
                'count': count,
                'category': triathlon.get('category', 'Races')
            })

    return achievements

def process_dataframe(dataframe):
    # Ensure necessary columns are present
    required_columns = ['Calories', 'Distance', 'Elapsed Time', 'Elevation Gain', 'Average Heart Rate', 'Activity Date', 'Activity Type']
    missing_columns = [col for col in required_columns if col not in dataframe.columns]
    if missing_columns:
        error = f"The following required columns are missing in the uploaded file: {', '.join(missing_columns)}"
        return None, error

    # Convert necessary columns to numeric, handling errors
    numeric_columns = ['Calories', 'Distance', 'Elapsed Time', 'Elevation Gain', 'Average Heart Rate']
    for col in numeric_columns:
        dataframe[col] = pd.to_numeric(dataframe[col], errors='coerce')

    # Drop rows with NaN values in numeric columns
    dataframe = dataframe.dropna(subset=numeric_columns)

    # Convert 'Activity Date' to datetime
    dataframe['Activity Date'] = pd.to_datetime(dataframe['Activity Date'], errors='coerce')

    # Drop rows with invalid dates
    dataframe = dataframe.dropna(subset=['Activity Date'])

    # Ensure 'Activity Type' is a string
    dataframe['Activity Type'] = dataframe['Activity Type'].astype(str)

    # Check if DataFrame is empty
    if dataframe.empty:
        error = 'No valid data found after processing. Please check your CSV file.'
        return None, error

    return dataframe, None

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
            # Read the CSV file into a DataFrame
            try:
                dataframe = pd.read_csv(file)
                dataframe, error = process_dataframe(dataframe)
                if error:
                    return render_template('index.html', error=error)
                # Proceed with processing
                # [Include your existing data processing code here]
                # ...
                return render_template('dashboard.html',
                                       user_rank=user_rank,
                                       total_hours=total_hours,
                                       stats=stats,
                                       achievements_by_period=achievements_by_period,
                                       coins_by_period=coins_by_period,
                                       period_names=period_names,
                                       periods=periods)
            except Exception as e:
                error = f'An error occurred during processing: {e}'
                return render_template('index.html', error=error)
        else:
            error = 'Invalid file type. Please upload a CSV file.'
            return render_template('index.html', error=error)
    else:
        # GET request, show the file upload form
        return render_template('index.html')

if __name__ == '__main__':
    app.run()
