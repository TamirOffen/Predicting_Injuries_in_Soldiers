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

    # Ensure axes is always iterable
    if rows == 1:
        axes = [axes]  # Convert to a list of length 1
    elif num_days == 1:
        axes = [axes]  # Also handle the case where num_days == 1

    for i, day in enumerate(days):
        # print(type(axes))
        ax1, ax2 = axes[i]

        # Visualization from visualize_week (left side)
        filtered_df = user_sleep_readable[soldier_id]['weeks'][week_num][
            user_sleep_readable[soldier_id]['weeks'][week_num]['datetime'].dt.date == day
            ]
        if week_num in sleep_hr_dict[soldier_id]['weeks'].keys():
            hr_steps_df = sleep_hr_dict[soldier_id]['weeks'][week_num]
        else:
            hr_steps_df = pd.DataFrame()
        if hr_steps_df.empty:
            combined_df = filtered_df.copy()
            combined_df['pulse'] = pd.Series([pd.NA] * len(combined_df))
            combined_df['steps'] = pd.Series([pd.NA] * len(combined_df))
        # print(hr_steps_df)
        else:
            combined_df = pd.merge(
                filtered_df,
                hr_steps_df,
                on='datetime',
                how='left'
            )
            combined_df = combined_df.drop(columns=['Hour', 'Min', 'startTimeDate'], errors='ignore')

        for j, row in combined_df.iterrows():
            if row['SleepState'] == 1:
                color = 'red'  # sleeping
            elif row['SleepState'] == 0:
                color = 'green'  # awake
            else:
                color = 'yellow'  # not known

            ax1.fill_between([row['datetime'], row['datetime'] + timedelta(minutes=1)], 0, 1, color=color)

        ax1.set_xlabel('Time')
        ax1.set_yticks([0, 1])
        ax1.set_yticklabels(['', ''])
        ax1.set_ylim(0, 1)
        ax1.set_title(day.strftime('%Y-%m-%d'))
        ax1.tick_params(axis='x', rotation=45)

        ax1_twin = ax1.twinx()
        ax1_twin.grid(False)
        if not combined_df['pulse'].isna().all():
            ax1_twin.plot(combined_df['datetime'], combined_df['pulse'], color='blue', label='Heart Rate',
                          linestyle='-')
        ax1_twin.tick_params(axis='y', labelcolor='blue')

        # Create a third y-axis for steps
        ax3 = ax1.twinx()
        ax3.grid(False)
        ax3.spines['right'].set_position(('outward', 40))  # Offset the third y-axis to avoid overlap
        ax3.spines['right'].set_visible(True)  # Ensure the right spine is visible

        # Plot steps data
        if not combined_df['steps'].isna().all():
            ax3.plot(combined_df['datetime'], combined_df['steps'], color='purple', label='Steps', linestyle='--')
        ax3.set_ylabel('', color='purple')
        ax3.tick_params(axis='y', labelcolor='purple')

        # Add legends
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        lines3, labels3 = ax3.get_legend_handles_labels()
        # ax1.legend(lines + lines2 + lines3, labels + labels2 + labels3, loc='upper left')
        awake_patch = plt.Line2D([0], [0], color='green', lw=4, label='Awake')
        sleeping_patch = plt.Line2D([0], [0], color='red', lw=4, label='Sleeping')
        unknown_patch = plt.Line2D([0], [0], color='yellow', lw=4, label='Unknown')

        ax1.legend([awake_patch, sleeping_patch, unknown_patch] + lines + lines2 + lines3,
                   ['Awake', 'Sleeping', 'Unknown'] + labels + labels2 + labels3, loc='upper left')

        # Visualization from visualize_sleep_imputation (right side)
        filtered_df_copy = filtered_df.copy()
        filtered_df_copy.drop_duplicates(subset=['datetime'], inplace=True)

        pre_df = soldiers_unprocessed[soldier_id]['sleep']['sleep'][week_num].copy()
        pre_df['datetime'] = pd.to_datetime(pre_df['Date']) + pd.to_timedelta(pre_df['Hour'],
                                                                              unit='h') + pd.to_timedelta(
            pre_df['Minute'], unit='m')
        pre_df.drop_duplicates(subset=['datetime'], inplace=True)
        combined_df = pd.merge(
            filtered_df_copy,
            pre_df,
            on='datetime',
            how='left'
        )

        for idx, row in combined_df.iterrows():
            if row['SleepState_y'] == 'Awake':
                combined_df.at[idx, 'SleepState_y'] = 0
            elif row['SleepState_y'] in ['Light Sleep', 'Deep Sleep']:
                combined_df.at[idx, 'SleepState_y'] = 1

        combined_df['imputation'] = (combined_df['SleepState_x'] != 2) & (
                    combined_df['SleepState_x'] != combined_df['SleepState_y'])

        if hr_steps_df.empty:
            combined_hr_df = combined_df.copy()
            combined_hr_df['pulse'] = pd.Series([pd.NA] * len(combined_hr_df))
        else:
            combined_hr_df = pd.merge(
                combined_df,
                hr_steps_df,
                on='datetime',
                how='left'
            )

        for j, row in combined_hr_df.iterrows():
            if row['SleepState_x'] == 2:
                ax2.fill_between([row['datetime'], row['datetime'] + timedelta(minutes=1)], 0, 1, color='black')
            elif not row['imputation']:
                ax2.fill_between([row['datetime'], row['datetime'] + timedelta(minutes=1)], 0, 1, color='blue')
            elif row['imputation']:
                ax2.fill_between([row['datetime'], row['datetime'] + timedelta(minutes=1)], 0, 1, color='orange')

        ax2.set_xlabel('Time')
        ax2.set_yticks([0, 1])
        ax2.set_yticklabels(['', ''])
        ax2.set_ylim(0, 1)
        ax2.set_title(day.strftime('%Y-%m-%d'))
        ax2.tick_params(axis='x', rotation=45)

        ax2_twin = ax2.twinx()
        ax2_twin.grid(False)
        if not combined_hr_df['pulse'].isna().all():
            ax2_twin.plot(combined_hr_df['datetime'], combined_hr_df['pulse'], color='yellow', label='Heart Rate',
                          linestyle='-')
        ax2_twin.tick_params(axis='y', labelcolor='black')

        imp_patch = plt.Line2D([0], [0], color='orange', lw=4, label='New')
        no_imp_patch = plt.Line2D([0], [0], color='blue', lw=4, label='Original')
        no_info_patch = plt.Line2D([0], [0], color='black', lw=4, label='Not Enough Info')
        hr_patch = plt.Line2D([0], [0], color='yellow', lw=1, label='Heart Rate')
        ax2.legend([no_imp_patch, imp_patch, no_info_patch, hr_patch],
                   ['Original', 'New', 'Not Enough Info', 'Heart Rate'], loc='upper left')

    fig.suptitle(f'Sleep & Imputation Visualization for Soldier \'{soldier_id}\'\nweek no. {week_num}', fontsize=16)
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

