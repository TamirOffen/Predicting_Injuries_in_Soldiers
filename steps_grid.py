import pandas as pd
import pickle
import os


# usage:
# python steps_grid.py
# when epochs.csv is located in data folder
# or
# python steps_grid.py --file_path path/to/epochs.csv

def preprocess_epochs(file_path='data/epochs.csv'):
    # Load dataset
    print(f'loading dataset at path: {file_path}')
    df = pd.read_csv(file_path)

    users_weekly_epoch = {}

    print(f'dataset loaded, starting preprocessing...')
    df = df[df['startTimeOffsetInSeconds'].isin([7200, 10800])]
    df['startTimeLocal'] = pd.to_datetime(df['startTimeInSeconds'] + df['startTimeOffsetInSeconds'], unit='s')
    df = df.drop(['startTimeInSeconds', 'startTimeOffsetInSeconds'], axis=1)

    # Returns the week number (1,52) of the date.
    # Assuming week starts on a Sunday, and not a Monday.
    def get_week_number(date):
        adjusted_date = date - pd.Timedelta(days=(date.weekday() + 1) % 7)  # date of closest, prev Sunday
        return adjusted_date.isocalendar()[1]

    df['WeekNumber'] = df['startTimeLocal'].apply(get_week_number)

    agg_dict = {
        'steps': 'sum',
        'userId': 'first',
        'activeTimeInSeconds': 'sum',
        'distanceInMeters': 'sum'
    }

    for user, user_df in df.groupby('userId'):
        weekly_user_df = {}
        for week_num, week_df in user_df.groupby('WeekNumber'):
            weekly_df = week_df.groupby('startTimeLocal').agg(agg_dict).reset_index()
            # Speed calculation:
            filtered_df = week_df[week_df['activityType'].isin(['WALKING', 'RUNNING'])]
            grouped_df = filtered_df.groupby('startTimeLocal').agg(
                {'activeTimeInSeconds': 'sum', 'distanceInMeters': 'sum'}).reset_index()
            grouped_df['speed'] = (grouped_df['distanceInMeters'] / grouped_df[
                'activeTimeInSeconds']) * 3.6  # convert from m/s to km/h
            weekly_df = weekly_df.merge(grouped_df[['startTimeLocal', 'speed']], on='startTimeLocal', how='left')
            weekly_df['speed'] = weekly_df['speed'].fillna(0)
            weekly_df['is_running'] = weekly_df['speed'] >= 7.5

            weekly_user_df[week_num] = weekly_df

        users_weekly_epoch[user] = weekly_user_df

    with open('steps_grid.pkl', 'wb') as file:
        pickle.dump(users_weekly_epoch, file)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, default='data/epochs.csv')
    args = parser.parse_args()

    file_path = args.file_path
    if not os.path.exists(file_path):
        print(f"file not found: {file_path}")
    else:
        preprocess_epochs(file_path)
        print("processing complete. output saved to steps.pkl.")
