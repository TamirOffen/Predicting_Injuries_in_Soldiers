import pandas as pd
import datetime
import pickle
import os


# usage:
# python heart_rate_grid.py
# when both heart_rate_daily.csv and dailies_summary.csv are located in 'data' folder
# or
# python heart_rate_grid.py --data_folder_path path/to/data


def convert_unix_to_datetime(unix_timestamp):
    return datetime.datetime.fromtimestamp(unix_timestamp)


# returns the week number (1,52) of the date.
# assuming week starts on a sunday, and not a monday.
def get_week_number(date):
    adjusted_date = date - pd.Timedelta(days=(date.weekday() + 1) % 7)  # date of closest, prev sunday
    return adjusted_date.isocalendar()[1]


# important note: 'calendarDate' is already the local time, so no need to use startTimeOffsetInSeconds.
def add_date_to_df(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """
    if df1 is heart_rate_daily.csv and df2 is dailies_summary.csv, then date+time column is added to df1, along with the week number
    :param df1: heart rate daily
    :param df2: daily summary
    :return: df1 with datetime and WeekNumber columns
    """
    # Create a dictionary that maps 'summaryId' to 'calendarDate' in df2
    date_dict = df2.set_index('summaryId')['calendarDate'].to_dict()

    # Add a new column 'date' to df1 by mapping 'dailiessummaryId' to 'calendarDate' using date_dict
    df1['date'] = df1['dailiessummaryId'].map(date_dict)
    df1['date'] = pd.to_datetime(df1['date'])

    # Convert 'timeOffsetHeartRateSample' from seconds to timedelta
    df1['time'] = pd.to_timedelta(df1['timeOffsetHeartRateSamples'], unit='s')

    # Add 'date' and 'timeOffsetHeartRateSample' to create a datetime representing the time of day
    df1['datetime'] = df1['date'] + df1['time']

    # about 0.01 percent of rows are NaN in 'datetime', so remove them.
    df1 = df1.dropna(subset=['datetime']).copy()

    # add week number
    df1['WeekNumber'] = df1['datetime'].apply(get_week_number)

    df1.drop(columns=['time', 'date', 'timeOffsetHeartRateSamples'], errors='ignore', inplace=True)

    return df1


def analyze_heart_rate(df, dailies):
    return add_date_to_df(df, dailies)


def preprocess_hr(data_folder_path):
    # loading heart_rate_daily.csv and dailies_summary.csv datasets
    if not os.path.exists(f'{data_folder_path}/heart_rate_daily.csv'):
        print(f'heart_rate_daily.csv dataset not found in {data_folder_path}')
    else:
        print(f'loading heart_rate_daily.csv')
        df_heartrate = pd.read_csv('data/heart_rate_daily.csv')

    if not os.path.exists(f'{data_folder_path}/dailies_summary.csv'):
        print(f'dailies_summary.csv dataset not found in {data_folder_path}')
    else:
        print(f'loading dailies_summary.csv')
        df_dailies = pd.read_csv('data/dailies_summary.csv')

    print(f'adding date and week number to heart_rate_daily.csv from dailies_summary.csv')
    heart_rate_df = analyze_heart_rate(df_heartrate, df_dailies)

    print(f'creating grid...')
    users_weekly_hr = {}
    for user, user_df in heart_rate_df.groupby('userId'):
        weekly_user_df = {}
        for week_num, week_df in user_df.groupby('WeekNumber'):
            week_df = week_df.reset_index(drop=True)  # reset index to start at 0
            weekly_user_df[week_num] = week_df
        users_weekly_hr[user] = weekly_user_df

    pickle_file_path = 'heart_rate_grid.pkl'
    with open(pickle_file_path, 'wb') as file:
        pickle.dump(users_weekly_hr, file)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--data_folder_path', type=str, default='data')
    args = parser.parse_args()

    data_folder_path = args.data_folder_path
    if not os.path.isdir(data_folder_path):
        print(f"Directory not found: {data_folder_path}")
    else:
        preprocess_hr(data_folder_path)
        print("Processing complete. Output saved to heart_rate_grid.pkl.")



