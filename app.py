from flask import Flask, render_template, request
import pandas as pd
from werkzeug.utils import secure_filename
import logging
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

app = Flask(__name__)

# Configuration
ALLOWED_EXTENSIONS = {'csv'}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 Megabytes

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Database URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    rank_name = db.Column(db.String(100), nullable=False)
    rank_emoji = db.Column(db.String(10), nullable=False)
    total_hours = db.Column(db.Float, nullable=False)
    coins = db.Column(db.PickleType, nullable=False)          # Changed to PickleType
    achievements = db.Column(db.PickleType, nullable=False)   # Changed to PickleType

    def __repr__(self):
        return f'<User {self.username}>'


# Initialize logging
logging.basicConfig(level=logging.INFO)

# Sample user data
users = [
    {
        'username': 'Alice',
        'rank': {'name': 'Gold 1', 'emoji': '🥇'},
        'coins': [
            {'name': 'Everest Coins', 'emoji': '🏔️', 'count': 5.0},
            {'name': 'Pizza Coins', 'emoji': '🍕', 'count': 10},
            {'name': 'Heartbeat Coins', 'emoji': '❤️', 'count': '15.0M'},
        ],
        'achievements': [
            {'name': 'Marathon Master', 'emoji': '4️⃣2️⃣🏃', 'count': 1},
            {'name': 'Climbing King', 'emoji': '🧗‍♂️', 'count': 3},
        ]
    },
    {
        'username': 'Bob',
        'rank': {'name': 'Silver 2', 'emoji': '🥈'},
        'coins': [
            {'name': 'Everest Coins', 'emoji': '🏔️', 'count': 2.5},
            {'name': 'Pizza Coins', 'emoji': '🍕', 'count': 8},
            {'name': 'Heartbeat Coins', 'emoji': '❤️', 'count': '10.0M'},
        ],
        'achievements': [
            {'name': 'Half Marathon Master', 'emoji': '2️⃣1️⃣🏃', 'count': 2},
            {'name': 'Speedster', 'emoji': '🏎️', 'count': 1},
        ]
    },
    # Add more users as needed
]


# Configuration
ALLOWED_EXTENSIONS = {'csv'}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 Megabytes

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Rank System Configuration in Python (Based on Total Hours)
rank_config = [
    {'name': 'Bronze 3', 'emoji': '🥉', 'min_hours': 0},
    {'name': 'Bronze 2', 'emoji': '🥉', 'min_hours': 50},   # 5*10
    {'name': 'Bronze 1', 'emoji': '🥉', 'min_hours': 100},  # 10*10
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
        'min_hours': 1050 + (i - 1) * 50  # Each level requires 50 additional hours
    })

# Achievement Configuration
# Achievement Configuration
achievement_config = {
    'longestStreak': {
        'name': 'Longest Streak',
        'emoji': '🔥',
        'count': 0
    },
    'distanceBadges': [
        {'name': '100 km', 'emoji': '💯', 'threshold': 100, 'count': 0},
        {'name': '200 km', 'emoji': '🔱', 'threshold': 200, 'count': 0},
        {'name': '300 km', 'emoji': '⚜️', 'threshold': 300, 'count': 0},
    ],
    'durationBadges': [
        {'name': '3 Hours', 'emoji': '⌛', 'threshold': 180, 'count': 0},  # 180 minutes
        {'name': '6 Hours', 'emoji': '⏱️', 'threshold': 360, 'count': 0},  # 360 minutes
        {'name': '12 Hours', 'emoji': '🌇', 'threshold': 720, 'count': 0},  # 720 minutes
    ],
    'weeklyBadges': [
        {'name': '5 Hours Week', 'emoji': '💰', 'threshold': 5, 'count': 0},   # 5 hours per week
        {'name': '10 Hours Week', 'emoji': '🧈', 'threshold': 10, 'count': 0},  # 10 hours per week
        {'name': '20 Hours Week', 'emoji': '💎', 'threshold': 20, 'count': 0},  # 20 hours per week
    ],
    'specialOccasions': [
        {'name': 'New Year Run', 'emoji': '🎉', 'dates': ['01-01'], 'count': 0},
        {'name': 'Christmas Run', 'emoji': '🎄', 'dates': ['12-25'], 'count': 0},
        # Add more special occasions as needed
    ],
    'additionalAchievements': [
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
            'emoji': '2️⃣1️⃣🏃',
            'description': 'Completed a half marathon (21.0975 km)',
            'count': 0,
            'type': 'Run',  # Specify the activity type
            'distance': 21097.5  # Half marathon distance in meters
        },
        {
            'name': 'Climbing King',
            'emoji': '🧗‍♂️',
            'description': 'Total elevation gain over 1000m',
            'count': 0
        },
        {
            'name': 'Speedster',
            'emoji': '🏎️',
            'description': 'Achieved an average speed over 30 km/h',
            'count': 0
        },
        {
            'name': 'Consistency Champion',
            'emoji': '🔁',
            'description': 'Logged activities every day for a month',
            'count': 0
        },
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
        'total_calories': int(df['Calories'].sum()),
        'total_distance': int(df['Distance'].sum() / 1000),  # in km, integer
        'total_time': int(df['Elapsed Time'].sum() / 3600),  # in hours, integer
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

    # Coins collected in the last 30 days
    last_month = pd.Timestamp.now() - pd.Timedelta(days=30)
    coins_last_month_df = df[df['Activity Date'] >= last_month]
    everest_coins_last_month = coins_last_month_df['Total Elevation Gain'].sum() / EVEREST_HEIGHT
    pizza_coins_last_month = coins_last_month_df['Calories'].sum() / PIZZA_CALORIES
    heartbeat_coins_last_month = coins_last_month_df['Total Heartbeats'].sum() / HEARTBEAT_UNIT

    coins = [
        {
            'name': 'Everest Coins',
            'emoji': '🏔️',
            'count': round(everest_coins, 1),  # Keep one decimal
            'last_month': round(everest_coins_last_month, 1)
        },
        {
            'name': 'Pizza Coins',
            'emoji': '🍕',
            'count': int(pizza_coins),  # No decimals
            'last_month': int(pizza_coins_last_month)
        },
        {
            'name': 'Heartbeat Coins',
            'emoji': '❤️',
            'count': round(heartbeat_coins / 1000000, 1),  # Keep as float for frontend formatting
            'last_month': round(heartbeat_coins_last_month / 1000000, 1)
        },
        {
            'name': 'Climber Activities',
            'emoji': '⛰️',
            'count': climber_coin,  # Integer
            'last_month': 0  # Integer
        },
        {
            'name': 'Michelin Star Burner',
            'emoji': '🔥',
            'count': michelin_star_coin,  # Integer
            'last_month': 0  # Integer
        }
    ]

    return coins


def calculate_achievements(df, achievement_config):
    """
    Calculates achievements based on the provided activities DataFrame and updates the achievement_config.
    """
    # Reset counts
    achievement_config['longestStreak']['count'] = 0
    for badge in achievement_config['distanceBadges']:
        badge['count'] = 0
    for badge in achievement_config['durationBadges']:
        badge['count'] = 0
    for badge in achievement_config['weeklyBadges']:
        badge['count'] = 0
    for badge in achievement_config['specialOccasions']:
        badge['count'] = 0
    for badge in achievement_config['additionalAchievements']:
        badge['count'] = 0

    # Calculate Longest Streak
    df_sorted = df.sort_values('Activity Date')
    unique_dates = df_sorted['Activity Date'].dt.date.unique()
    current_streak = 1
    max_streak = 1
    for i in range(1, len(unique_dates)):
        delta = (unique_dates[i] - unique_dates[i - 1]).days
        if delta == 1:
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
        else:
            current_streak = 1
    achievement_config['longestStreak']['count'] = max_streak

    # Calculate Distance Badges
    total_distance_km = df['Distance'].sum() / 1000  # Convert meters to kilometers
    for badge in achievement_config['distanceBadges']:
        badge['count'] = int(total_distance_km // badge['threshold'])

    # Calculate Duration Badges
    total_duration_minutes = df['Elapsed Time'].sum() / 60  # Convert seconds to minutes
    for badge in achievement_config['durationBadges']:
        badge['count'] = int(total_duration_minutes // badge['threshold'])

    # Calculate Weekly Badges
    df_sorted['Week'] = df_sorted['Activity Date'].dt.isocalendar().week
    weekly_hours = df_sorted.groupby('Week')['Elapsed Time'].sum() / 3600  # Convert seconds to hours
    for badge in achievement_config['weeklyBadges']:
        badge['count'] = int((weekly_hours >= badge['threshold']).sum())

    # Calculate Special Occasion Badges
    df_sorted['Month-Day'] = df_sorted['Activity Date'].dt.strftime('%m-%d')
    for badge in achievement_config['specialOccasions']:
        badge['count'] = (df_sorted['Month-Day'] == badge['dates'][0]).sum()
        # If multiple dates, you can modify the logic accordingly

    # Calculate Additional Achievements
    for badge in achievement_config['additionalAchievements']:
        if badge['name'] in ['Marathon Master', 'Half Marathon Master']:
            qualifying_activities = df_sorted[
                (df_sorted['Activity Type'].str.lower() == badge['type'].lower()) &
                (df_sorted['Distance'] >= badge['distance'])
            ]
            unique_days = qualifying_activities['Activity Date'].dt.date.nunique()
            badge['count'] = unique_days
        elif badge['name'] == 'Climbing King':
            total_elevation = df_sorted['Elevation Gain'].sum()
            badge['count'] = total_elevation // 1000  # Integer division
        elif badge['name'] == 'Speedster':
            df_sorted['Speed'] = df_sorted['Distance'] / df_sorted['Elapsed Time'] * 3600 / 1000  # km/h
            speed_achievements = df_sorted[df_sorted['Speed'] > 30]
            badge['count'] = speed_achievements.shape[0]
        elif badge['name'] == 'Consistency Champion':
            # Check for at least one activity every day for any 30-day window
            activity_dates = sorted(df_sorted['Activity Date'].dt.date.unique())
            streak = 0
            for i in range(1, len(activity_dates)):
                delta = (activity_dates[i] - activity_dates[i - 1]).days
                if delta == 1:
                    streak += 1
                else:
                    streak = 0
                if streak >= 29:  # 30 consecutive days
                    badge['count'] += 1
                    streak = 0  # Reset after achieving
        # Add more cases if you have additional achievements

    return achievement_config


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

def calculate_hours_last_month(df):
    last_month = pd.Timestamp.now() - pd.Timedelta(days=30)
    hours_last_month = df[df['Activity Date'] >= last_month]['Elapsed Time'].sum() / 3600
    return round(hours_last_month, 2)

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
        username = request.form.get('username')
        if not username:
            error = 'Please enter a username.'
            return render_template('index.html', error=error)

        # Rest of your file upload code...
        if 'file' not in request.files:
            error = 'No file part in the request.'
            return render_template('index.html', error=error)
        file = request.files['file']
        if file.filename == '':
            error = 'No file selected.'
            return render_template('index.html', error=error)
        if file and allowed_file(file.filename):
            # Process the file
            try:
                dataframe = pd.read_csv(file)
                dataframe, error = process_dataframe(dataframe)
                if error:
                    return render_template('index.html', error=error)

                # Proceed with processing
                achievements = calculate_achievements(dataframe, achievement_config.copy())
                coins = calculate_coins(dataframe)
                stats = calculate_stats(dataframe)
                total_hours = calculate_hours_total(dataframe)
                hours_last_month = calculate_hours_last_month(dataframe)
                user_rank = get_user_rank(total_hours, rank_config)
                progress, hours_next_level = calculate_progress(total_hours, rank_config)

                # Save user data to the database
                user = User(
                    username=username,
                    rank_name=user_rank['name'],
                    rank_emoji=user_rank['emoji'],
                    total_hours=total_hours,
                    coins=coins,
                    achievements=achievements
                )
                db.session.add(user)
                db.session.commit()

                # Render the dashboard
                return render_template('dashboard.html',
                                       user_rank=user_rank,
                                       total_hours=total_hours,
                                       stats=stats,
                                       achievements=achievements,
                                       coins=coins,
                                       progress=progress,
                                       hours_next_level=hours_next_level,
                                       hours_last_month=hours_last_month)
            except Exception as e:
                logging.exception("Error processing the file.")
                error = f'An error occurred during processing: {e}'
                return render_template('index.html', error=error)
        else:
            error = 'Invalid file type. Please upload a CSV file.'
            return render_template('index.html', error=error)
    else:
        return render_template('index.html')



# Route for the leaderboard
@app.route('/leaderboard')
def leaderboard():
    # Retrieve all users from the database
    users = User.query.all()

    # Create a rank order mapping
    rank_order = {rank['name']: index for index, rank in enumerate(rank_config)}

    # Function to get rank index
    def get_rank_index(rank_name):
        return rank_order.get(rank_name, len(rank_order))

    # Sort users by rank
    sorted_users = sorted(users, key=lambda x: get_rank_index(x.rank_name))

    return render_template('leaderboard.html', users=sorted_users)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Creates the tables if they don't exist
    app.run(debug=True)
