# Predicting Injuries Among Combat Soldiers

This repository contains the code and documentation for a project that aims to forecast injuries and identify critical factors affecting soldier health. By analyzing wearable data collected from Golani troops, the study seeks to enhance injury prevention and resource allocation strategies.

## Overview

Combat soldiers face a high risk of injuries, which can affect their health and the operational effectiveness of their units. This project applies machine learning models to large-scale real-world data collected from wearable devices to predict injuries and gain insights into their causes.

## Key Features

- **Data Processing**:
  - Organized raw data from Garmin wearables into weekly grids:
    - **Steps**: 15-minute intervals
    - **Heart Rate**: 15-second intervals
    - **Sleep**: 1-minute intervals
  - Addressed missing data in sleep grids through imputation, incorporating heart rate and step data.
- **Feature Engineering**:
  - Extracted features like speed and activity classification.
  - Validated correlations between speed, heart rate, and physical activity patterns.
- **Preliminary Modeling**:
  - In the process of developing an Autoencoder to explore latent space representations of heart rate data, with the goal of identifying high-risk groups for injuries.

## Notebooks

- `steps_from_epochs.ipynb`: Step grid creation and preprocessing.
- `create_heartrate_grid.ipynb`: Heart rate grid organization and preprocessing.
- `create_sleeping_grid.ipynb`: Sleep grid generation.
- `completing_sleep.ipynb`: Imputation of missing sleep data.
- `All_Soldiers_Sleep_Vis.py`: Visualizations of sleep grids before and after imputation.

## Results

The preprocessing steps resulted in clean, structured grids ready for use in machine learning models. Correlations between physical activity, heart rate, and sleep patterns were validated and visualized, forming a strong foundation for predictive modeling.

## Collaborators and Funding

- **Funding**: Sponsored by the IDF.
- **Collaborators**: A joint initiative between Haifa University's Physical Therapy Lab and Technion's VISTA Lab.
- **Advisor**: Barak Gahtan, PhD student under Alex Bronstein.
