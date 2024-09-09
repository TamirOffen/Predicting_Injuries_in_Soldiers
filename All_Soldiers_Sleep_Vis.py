### For all soldiers, creates sleep + sleep imputation visualizations ###

import matplotlib.pyplot as plt
import pandas as pd
from datetime import timedelta
import os
from tqdm import tqdm


# displays both visualization side by side
def display_both(soldier_id, week_num, save_as_png=False, output_folder=""):
    """
    Displays both Sleep and Sleep Imputation visualizations for soldier_id at week_num
    :param save_as_png: if true, output will be saved to output_folder as output_folder/soldier_id/week_num.png
    """
    if soldier_id not in user_sleep_readable.keys():
        print(f'{soldier_id} does not have sleep data')
        return
    if week_num not in user_sleep_readable[soldier_id]['weeks']:
        print(f'Error: soldier {soldier_id} does not have data for week no. {week_num}')
        s = 'weeks'
        print(f'Weeks available for soldier: {list(user_sleep_readable[soldier_id][s].keys())}')
        return

    days = sorted(set(user_sleep_readable[soldier_id]['weeks'][week_num]['datetime'].dt.date))

    num_days = len(days)
    cols = 2  # Number of columns in the subplot grid (one for each function)
    rows = num_days  # One row per day

    fig, axes = plt.subplots(rows, cols, figsize=(30, 5 * rows), sharex=False, sharey=False)

    # Ensure axes is always a 2D array
    if rows == 1 and cols == 1:
        axes = [[axes]]  # Convert to a 2D array
    elif rows == 1:
        axes = [axes]  # Convert to a list of length 1
    elif cols == 1:
        axes = [[ax] for ax in axes]  # Convert to a list of lists

    for i, day in enumerate(days):
        ax1, ax2 = axes[i]

        # Visualization from the first function (left side)
        to_plot = soldiers_unprocessed[soldier_id]['sleep']['sleep'][week_num].copy()
        to_plot['datetime'] = pd.to_datetime(to_plot['Date']) + pd.to_timedelta(to_plot['Hour'],
                                                                                unit='h') + pd.to_timedelta(
            to_plot['Minute'], unit='m')
        to_plot.drop_duplicates(subset=['datetime'], inplace=True)
        to_plot = to_plot[
            to_plot['datetime'].dt.date == day
            ]

        if soldier_id in sleep_hr_dict and week_num in sleep_hr_dict[soldier_id]['weeks'] and not \
        sleep_hr_dict[soldier_id]['weeks'][week_num].empty:
            hr_steps_df = sleep_hr_dict[soldier_id]['weeks'][week_num]
            # Perform the merge with steps data
            combined_df = pd.merge(
                to_plot,
                hr_steps_df,
                on='datetime',
                how='left'  # left join, keeps all the sleep data; missing data will be NaN.
            )
        else:
            # If no steps data, use final_df only
            combined_df = to_plot.copy()
            combined_df['pulse'] = None  # Create a 'steps' column with None or NaN for missing steps data

        to_plot = combined_df
        for j, row in to_plot.iterrows():
            if row['SleepState'] == '?':
                ax1.fill_between([row['datetime'], row['datetime'] + timedelta(minutes=1)], 0, 1, color='black')
            elif row['SleepState'] == 'Awake':
                ax1.fill_between([row['datetime'], row['datetime'] + timedelta(minutes=1)], 0, 1, color='green')
            else:
                ax1.fill_between([row['datetime'], row['datetime'] + timedelta(minutes=1)], 0, 1, color='red')

        # Customize the plot for sleep state
        ax1.set_xlabel('Time')
        ax1.set_ylabel('')
        ax1.set_yticks([0, 1])
        ax1.set_yticklabels(['', ''])
        ax1.set_ylim(0, 1)
        ax1.tick_params(axis='y')
        ax1.set_title(day.strftime('%Y-%m-%d'))

        # Format x-axis for better readability
        ax1.tick_params(axis='x', rotation=45)

        # Create a secondary y-axis for heart rate (hr) and steps
        ax1_1 = ax1.twinx()
        ax1_1.grid(False)  # Disable grid lines for ax2
        ax1_1.spines['top'].set_visible(True)  # Ensure the top spine is visible
        ax1_1.spines['left'].set_visible(True)  # Ensure the left spine is visible
        ax1_1.spines['right'].set_color('blue')  # Set right spine color for clarity
        ax1_1.spines['right'].set_visible(True)  # Ensure the right spine is visible

        # Plot heart rate data
        ax1_1.plot(to_plot['datetime'], to_plot['pulse'], color='blue', label='Heart Rate', linestyle='-')
        ax1_1.set_ylabel('', color='blue')
        ax1_1.tick_params(axis='y', labelcolor='blue')

        # Add legends
        awake_patch = plt.Line2D([0], [0], color='green', lw=4, label='Awake')
        sleeping_patch = plt.Line2D([0], [0], color='red', lw=4, label='Sleeping')
        unknown_patch = plt.Line2D([0], [0], color='black', lw=4, label='Unknown')
        pulse_line = plt.Line2D([0], [0], color='blue', lw=1, label='Pulse')

        ax1.legend([awake_patch, sleeping_patch, unknown_patch, pulse_line], ['Awake', 'Sleeping', 'Unknown', 'Pulse'],
                   loc='upper left')

        if i == 0:
            ax1.set_title(f"Sleep States before Processing\n\n{day}", fontsize=16)

        ###############
        # Visualization from the second function (right side)
        # Filter the DataFrame for a single day (date_to_filter)
        filtered_df_imputed = user_sleep_readable[soldier_id]['weeks'][week_num][
            user_sleep_readable[soldier_id]['weeks'][week_num]['datetime'].dt.date == day
            ].copy()
        filtered_df_imputed.drop_duplicates(subset=['datetime'], inplace=True)

        filtered_df_raw = soldiers_unprocessed[soldier_id]['sleep']['sleep'][week_num].copy()
        filtered_df_raw['datetime'] = pd.to_datetime(filtered_df_raw['Date']) + pd.to_timedelta(filtered_df_raw['Hour'],
                                                                                                unit='h') + pd.to_timedelta(
            filtered_df_raw['Minute'], unit='m')
        filtered_df_raw.drop_duplicates(subset=['datetime'], inplace=True)
        filtered_df_raw = filtered_df_raw[filtered_df_raw['datetime'].dt.date == day]
        filtered_df_raw.loc[filtered_df_raw['SleepState'].isin(['Light Sleep', 'Deep Sleep']), 'SleepState'] = 1
        filtered_df_raw.loc[filtered_df_raw['SleepState'] == 'Awake', 'SleepState'] = 0

        # Step 1: Merge the DataFrames on 'datetime'
        merged_df = pd.merge(filtered_df_raw[['datetime', 'SleepState']],
                             filtered_df_imputed[['datetime', 'SleepState']],
                             on='datetime',
                             suffixes=('_raw', '_imputed'))

        # Step 2: Define the logic for the 'state' column
        def determine_state(row):
            raw_state = row['SleepState_raw']
            imputed_state = row['SleepState_imputed']

            if raw_state == 1:
                return 0  # sleeping original
            elif raw_state == 0:
                return 2  # awake original
            elif imputed_state == 1:
                return 1  # sleeping imputed
            elif imputed_state == 0:
                return 3  # awake imputed
            elif imputed_state == 2:
                return 4  # still don't know

        # Step 3: Apply the logic to create the new column 'state'
        merged_df['state'] = merged_df.apply(determine_state, axis=1)

        # Step 4: Create the final DataFrame with 'datetime' and 'state'
        final_df = merged_df[['datetime', 'state']]

        # Check if the soldier_id exists in the sleep_hr_dict and if the week_num exists for that soldier
        if soldier_id in sleep_hr_dict and week_num in sleep_hr_dict[soldier_id]['weeks'] and not \
        sleep_hr_dict[soldier_id]['weeks'][week_num].empty:
            hr_steps_df = sleep_hr_dict[soldier_id]['weeks'][week_num]

            # Perform the merge with steps data
            combined_df = pd.merge(
                final_df,
                hr_steps_df,
                on='datetime',
                how='left'  # left join, keeps all the sleep data; missing data will be NaN.
            )
        else:
            # If no steps data, use final_df only
            combined_df = final_df.copy()
            combined_df['pulse'] = None  # Create a 'steps' column with None or NaN for missing steps data

        to_plot = combined_df  # sleep data in 'SleepState', hr data in 'pulse', steps count data in 'steps'
        # Plot sleep state as blocks of color
        # awake/0 in green, sleeping/1 in red, unknown/2 in yellow
        for j, row in to_plot.iterrows():
            if row['state'] == 0:
                color = 'red'  # sleeping original
            elif row['state'] == 1:
                color = 'lightcoral'  # sleeping imputed (lighter red)
            elif row['state'] == 2:
                color = 'green'  # awake original
            elif row['state'] == 3:
                color = 'lightgreen'  # awake imputed (lighter green)
            else:  # SleepState == 4
                color = 'black'  # still don't know

            # Plot with the color based on the SleepState
            ax2.fill_between([row['datetime'], row['datetime'] + timedelta(minutes=1)], 0, 1, color=color)

        # Customize the plot for sleep state
        ax2.set_xlabel('Time')
        ax2.set_ylabel('')
        ax2.set_yticks([0, 1])
        ax2.set_yticklabels(['', ''])
        ax2.set_ylim(0, 1)
        ax2.tick_params(axis='y')
        ax2.set_title(day.strftime('%Y-%m-%d'))

        # Format x-axis for better readability
        ax2.tick_params(axis='x', rotation=45)

        # Create a secondary y-axis for heart rate (hr) and steps
        ax2_1 = ax2.twinx()
        ax2_1.grid(False)  # Disable grid lines for ax2
        ax2_1.spines['top'].set_visible(True)  # Ensure the top spine is visible
        ax2_1.spines['left'].set_visible(True)  # Ensure the left spine is visible
        ax2_1.spines['right'].set_color('blue')  # Set right spine color for clarity
        ax2_1.spines['right'].set_visible(True)  # Ensure the right spine is visible

        # Plot heart rate data
        ax2_1.plot(to_plot['datetime'], to_plot['pulse'], color='blue', label='Heart Rate', linestyle='-')
        ax2_1.set_ylabel('', color='blue')
        ax2_1.tick_params(axis='y', labelcolor='blue')

        # Define the patches for the legend
        awake_patch = plt.Line2D([0], [0], color='green', lw=4, label='Awake Original')
        sleeping_patch = plt.Line2D([0], [0], color='red', lw=4, label='Sleeping Original')
        awake_imputed_patch = plt.Line2D([0], [0], color='lightgreen', lw=4, label='Awake Imputed')
        sleeping_imputed_patch = plt.Line2D([0], [0], color='lightcoral', lw=4, label='Sleeping Imputed')
        unknown_patch = plt.Line2D([0], [0], color='black', lw=4, label='Not Enough Info')
        pulse_line = plt.Line2D([0], [0], color='blue', lw=1, label='Pulse')

        # Combine everything in the legend, including the new patches
        ax2.legend(
            [awake_patch, sleeping_patch, awake_imputed_patch, sleeping_imputed_patch, unknown_patch, pulse_line],
            ['Awake Original', 'Sleeping Original', 'Awake Imputed', 'Sleeping Imputed', 'Not Enough Info', 'Pulse'],
            loc='upper left'
        )

        if i == 0:
            ax2.set_title(f"Sleep States after Processing\n\n{day}", fontsize=16)

    fig.suptitle(f'Sleep & Imputation Visualization for Soldier \'{soldier_id}\'\nweek no. {week_num}', fontsize=20)
    plt.tight_layout(rect=[0, 0.03, 1, 0.98])
    if save_as_png:
        directory = f'{output_folder}/{soldier_id}'
        os.makedirs(directory, exist_ok=True)
        plt.savefig(f'{directory}/{week_num}.png', format="png")
        plt.close()
    else:
        plt.show()


if __name__ == "__main__":
    # Data Loading:
    with tqdm(total=4, desc="Loading Datasets", unit="dataset") as pbar:
        # Load people_to_work_with dataset
        df_watches_data = pd.read_excel('Processed_data/additional_data.xlsx')
        people_to_work_with = set(df_watches_data['userId'])
        pbar.update(1)
        # print("loaded people_to_work_with dataset")

        # Load user_sleep_readable dataset
        input_file_sleep_weekly_012 = 'Processed_data/sleep_readable.pickle'  # File path of the pickle file
        with open(input_file_sleep_weekly_012, 'rb') as f:
            user_sleep_readable = pd.read_pickle(f)
        pbar.update(1)
        # print("loaded user_sleep_readable dataset")

        # Load sleep_hr_dict dataset
        steps_hr_file = 'Processed_data/merge_dict_hr_steps_distance.pickle'  # File path of the pickle file
        with open(steps_hr_file, 'rb') as f:
            sleep_hr_dict = pd.read_pickle(f)
        pbar.update(1)
        # print("loaded sleep_hr_dict dataset")

        # Load soldiers_unprocessed dataset
        with open('Processed_data/soldiers_unprocessed.pkl', 'rb') as file:
            soldiers_unprocessed = pd.read_pickle(file)
        pbar.update(1)
        # print("loaded soldiers_unprocessed dataset")

    print("\nCreating Sleep Visualization for each soldier:")
    for s in people_to_work_with:
        if s not in user_sleep_readable.keys():
            print(f'{s} does not have sleep data!')
            continue
        for w in tqdm(user_sleep_readable[s]['weeks'], desc=f'Processing {s}', unit='week'):
            display_both(s, w, save_as_png=True, output_folder="SleepVis")

