# import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sns
# from PostOpCareModel import PostOpCareModel
# import random # Needed for robust patient sampling
#
# # --- SIMULATION PARAMETERS ---
# NUM_PATIENTS = 100
# MAX_DAYS = 60
# PATIENT_ID_TO_TRACK = 0 # Default patient ID for the trajectory plot
#
# # --- EXECUTION ---
# print(f"Starting MAS simulation for {NUM_PATIENTS} patients over {MAX_DAYS} days...")
# model = PostOpCareModel(num_patients=NUM_PATIENTS, max_steps=MAX_DAYS)
#
# # Run the simulation step-by-step
# for i in range(MAX_DAYS):
#     if model.running:
#         model.step()
#     else:
#         break
#
# print("Simulation complete.")
#
#
# # --- DATA PROCESSING & CLEANING ---
# raw_agent_data = model.datacollector.get_agent_vars_dataframe().reset_index()
#
# # 1. Separate Patient Data (Percepts and FINAL Plan Used)
# patient_data_full = raw_agent_data.dropna(subset=['Mobility']).copy()
# patient_data_full = patient_data_full.rename(columns={'AgentID': 'Patient_ID', 'Day': 'Recovery_Day'})
#
# # 2. Separate Care Agent Data (CA Suggestion and Alert Status)
# care_agent_data = raw_agent_data.dropna(subset=['CA_Suggested_Medication']).copy()
# care_agent_data = care_agent_data[['Step', 'AgentID', 'CA_Suggested_Intensity', 'CA_Suggested_Medication', 'CA_Alert_Status']].rename(
#     columns={'AgentID': 'CareAgent_ID'}
# )
#
# # Merge Care Agent's suggestions (made at Step N) to the Patient's data (at Step N+1)
# care_agent_data['Step'] = care_agent_data['Step'] + 1
# final_trajectory_data = pd.merge(
#     patient_data_full,
#     care_agent_data[['Step', 'CA_Suggested_Intensity', 'CA_Suggested_Medication', 'CA_Alert_Status']],
#     on=['Step'],
#     how='left'
# )
#
# # Realign Patient_ID after merge (Patient ID = CareAgent ID - 1)
# final_trajectory_data['Patient_ID'] = final_trajectory_data['Patient_ID'].apply(lambda x: x if x % 2 == 0 else x - 1)
#
#
# # --- Final Cleaning for Analysis ---
# # Calculate the change in mobility from the plan used in the *previous* step
# final_trajectory_data['Mobility_Change'] = final_trajectory_data.groupby('Patient_ID')['Mobility'].diff()
# # Align the Plan_Used from Step N with the Mobility_Change that occurred in Step N+1
# final_trajectory_data['Previous_Plan_Used_Intensity'] = final_trajectory_data.groupby('Patient_ID')['Plan_Used_Intensity'].shift(1)
#
#
# # Get model data for macro reporting
# model_data = model.datacollector.get_model_vars_dataframe()
#
# # Access the raw agent data directly from the model's DataCollector for time series plots
# raw_agent_data_rerun = model.datacollector.get_agent_vars_dataframe().reset_index()
# patient_data_rerun = raw_agent_data_rerun[raw_agent_data_rerun['Mobility'].notna()].copy()
# final_step_patient_data_rerun = patient_data_rerun[patient_data_rerun['Step'] == MAX_DAYS].copy()
# final_step_patient_data_rerun = final_step_patient_data_rerun.rename(columns={'AgentID': 'Patient_ID'})
#
#
# # --- VISUALIZATION AND ANALYSIS (Plots 1-6) ---
#
# print("\n--- MAS Model and Trajectory Analysis ---")
#
# ## 1. Average Mobility Over Time (Macro Trend)
# print("\n1. Average Mobility Over Time (Macro Trend)")
# plt.figure(figsize=(8, 5))
# plt.plot(model_data.index, model_data['Average_Mobility'], label='Average Mobility')
# plt.xlabel("Step (Day)")
# plt.ylabel("Average Mobility Score")
# plt.title("1. Average Patient Mobility Over Time (Macro Trend)")
# plt.grid(True)
# plt.show()
#
# ## 2. Physician Intervention Count Over Time (MAS Metric)
# print("\n2. Physician Intervention Count Over Time (MAS Metric)")
# plt.figure(figsize=(8, 5))
# plt.plot(model_data.index, model_data['Physician_Intervention_Count'], color='tab:orange', label='Total Interventions')
# plt.xlabel("Step (Day)")
# plt.ylabel("Cumulative Interventions")
# plt.title("2. Physician Agent Interventions Over Time (MAS Metric)")
# plt.grid(True)
# plt.show()
#
#
# ## 3. Impact of Exercise Intensity on Mobility Change (Box Plot)
# print("\n3. Impact of Exercise Intensity on Mobility Change (Box Plot)")
# plt.figure(figsize=(8, 5))
# sns.boxplot(
#     x='Previous_Plan_Used_Intensity',
#     y='Mobility_Change',
#     data=final_trajectory_data.dropna(subset=['Previous_Plan_Used_Intensity', 'Mobility_Change'])
# )
# plt.xlabel("Previous Plan Used Intensity")
# plt.ylabel("Change in Mobility")
# plt.title("3. Impact of Exercise Intensity on Mobility Change")
# plt.grid(True)
# plt.show()
#
#
# ## 4. BP vs. Medication Dosage (MAS Monitoring Responsiveness)
# print("\n4. BP vs. Medication Dosage (MAS Monitoring Responsiveness)")
# plt.figure(figsize=(8, 5))
# sns.scatterplot(
#     x='BP',
#     y='Plan_Used_Medication',
#     data=final_trajectory_data[final_trajectory_data['BP'] > 120]
# )
# plt.xlabel("Blood Pressure (Patient Percept)")
# plt.ylabel("FINAL Medication Dosage (Agent Action)")
# plt.title("4. Agent Response: BP vs. FINAL Medication Dosage (BP > 120)")
# plt.grid(True)
# plt.show()
#
#
# # --- Time Series Plots (Plots 5 & 6) ---
#
# # Get all unique patient IDs from the final step data
# all_patient_ids = final_step_patient_data_rerun['Patient_ID'].unique()
# population_size = len(all_patient_ids)
#
# # FIX: Robust Patient Sampling Logic
# if population_size == 0:
#     num_patients_to_sample = 0
# elif population_size < 3:
#     num_patients_to_sample = population_size
# else:
#     num_patients_to_sample = min(5, population_size)
#
# selected_patient_ids = [10,20,30,40,50,60]
#
# if selected_patient_ids:
#     print("\n5 & 6. Trends of Blood Pressure and Body Temperature over time")
#     fig, axes = plt.subplots(2, 1, figsize=(10, 8)) # Use subplots and axes array for cleaner plotting
#
#     # Plot 5: Blood Pressure over time
#     for patient_id in selected_patient_ids:
#         # Use 'AgentID' for filtering patient_data_rerun
#         patient_trajectory = patient_data_rerun[patient_data_rerun['AgentID'] == patient_id]
#         axes[0].plot(patient_trajectory['Step'], patient_trajectory['BP'], label=f'Patient {int(patient_id)}')
#
#     axes[0].set_xlabel("Step (Day)")
#     axes[0].set_ylabel("Blood Pressure")
#     axes[0].set_title("5. Blood Pressure Over Time for Selected Patients")
#     axes[0].legend(loc='upper right', bbox_to_anchor=(1.25, 1))
#     axes[0].grid(True)
#
#     # Plot 6: Body Temperature over time
#     for patient_id in selected_patient_ids:
#         patient_trajectory = patient_data_rerun[patient_data_rerun['AgentID'] == patient_id]
#         axes[1].plot(patient_trajectory['Step'], patient_trajectory['Body_Temp'], label=f'Patient {int(patient_id)}')
#
#     axes[1].set_xlabel("Step (Day)")
#     axes[1].set_ylabel("Body Temperature (°C)")
#     axes[1].set_title("6. Body Temperature Over Time for Selected Patients")
#     axes[1].legend(loc='upper right', bbox_to_anchor=(1.25, 1))
#     axes[1].grid(True)
#
#     plt.tight_layout(rect=[0, 0, 0.9, 1]) # Adjust layout for legends
#     plt.show()
# else:
#     print("\nSkipping time series plots.")
#
#
# # --- Interactive Plot for Patient Trajectory (Plot 7) ---
#
# try:
#     # Logic to handle both interactive and non-interactive running
#     try:
#         patient_id_input = int(input(f"\n--- PLOT 7: PATIENT TRAJECTORY ---\nEnter the Patient ID to display trajectory trends (e.g., 0, 2, 4... up to {2*(NUM_PATIENTS-1)}): "))
#     except EOFError:
#         patient_id_input = PATIENT_ID_TO_TRACK
#         print(f"\n--- PLOT 7: PATIENT TRAJECTORY ---\nRunning non-interactively. Displaying Patient ID: {patient_id_input}")
#
#     patient_trajectory = final_trajectory_data[final_trajectory_data['Patient_ID'] == patient_id_input].copy()
#
#     # Columns for printing state (assuming Comorbidity is not collected)
#     state_columns = ['Mobility', 'Pain', 'Complication', 'BP', 'Body_Temp']
#
#     if not patient_trajectory.empty:
#         initial_condition = patient_trajectory.iloc[0]
#         final_condition = patient_trajectory.iloc[-1]
#
#         print(f"\n--- Initial Condition for Patient ID {patient_id_input} (Step {int(initial_condition['Step'])}) ---")
#         print(initial_condition[state_columns].to_markdown(numalign="left", stralign="left"))
#
#         print(f"\n--- Final Condition for Patient ID {patient_id_input} (Step {int(final_condition['Step'])}) ---")
#         print(final_condition[state_columns].to_markdown(numalign="left", stralign="left"))
#
#         print(f"\n7. Patient {patient_id_input} Trajectory: State vs. Final Agent Actions Over Time (MAS)")
#
#         fig, ax1 = plt.subplots(figsize=(12, 6))
#
#         # Plot Mobility and Pain on the first y-axis
#         ax1.plot(patient_trajectory['Step'], patient_trajectory['Mobility'], label='Mobility Score', color='tab:blue')
#         ax1.plot(patient_trajectory['Step'], patient_trajectory['Pain'], label='Pain Level', color='tab:red')
#         ax1.set_xlabel("Step (Day)")
#         ax1.set_ylabel("Patient State (1-10)", color='tab:blue')
#         ax1.tick_params(axis='y', labelcolor='tab:blue')
#         ax1.grid(True)
#
#         # Create a second y-axis for Suggested Plan (Intensity and Medication)
#         ax2 = ax1.twinx()
#         ax2.plot(patient_trajectory['Step'], patient_trajectory['Plan_Used_Intensity'], label='FINAL Exercise Intensity', color='tab:green', linestyle='-')
#         ax2.plot(patient_trajectory['Step'], patient_trajectory['Plan_Used_Medication'], label='FINAL Medication Dosage', color='tab:purple', linestyle='--')
#         ax2.set_ylabel("FINAL Plan Value", color="tab:green")
#         ax2.tick_params(axis='y', labelcolor='tab:green')
#
#         # Add title and legend
#         plt.title(f"7. Patient {int(patient_id_input)}: State vs. Final Agent Actions Over Time (MAS)")
#         fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
#
#         plt.show()
#
#     else:
#         print(f"Patient ID {patient_id_input} not found in the simulation data. Check if ID is an even number between 0 and {2*(NUM_PATIENTS-1)}.")
#
# except ValueError:
#     print("Invalid input. Please enter a valid integer Patient ID.")
import pandas as pd
from PostOpCareModel import PostOpCareModel
import random  # Needed for robust patient sampling

# --- SIMULATION PARAMETERS ---
NUM_PATIENTS = 100
MAX_DAYS = 60


def run_simulation_and_process_data(num_patients=NUM_PATIENTS, max_days=MAX_DAYS):
    """
    Runs the MAS simulation and processes the resulting data into clean DataFrames
    for visualization in the Streamlit app.

    Returns: final_trajectory_data, model_data, patient_data_rerun, final_step_patient_data_rerun
    """
    # Initialize and run the simulation model
    model = PostOpCareModel(num_patients=num_patients, max_steps=max_days)

    # Run the simulation step-by-step
    for i in range(max_days):
        if model.running:
            model.step()
        else:
            break

    # --- DATA PROCESSING & CLEANING ---
    raw_agent_data = model.datacollector.get_agent_vars_dataframe().reset_index()

    # 1. Separate Patient Data (Percepts and Plan to be used next)
    patient_data_full = raw_agent_data.dropna(subset=['Mobility']).copy()
    patient_data_full = patient_data_full.rename(columns={'AgentID': 'Patient_ID', 'Day': 'Recovery_Day'})

    # 2. Separate Care Agent Data (Not strictly needed for analysis but kept for debugging structure)
    # Care Agent IDs are odd numbers (1, 3, 5...)
    # We explicitly drop the data collection of Care Agent info from patient rows here,
    # but the patient_data_full is already clean of CA-specific columns.

    # --- Final Cleaning for Analysis (Focus on correct lag for actions) ---

    # 1. Calculate the change in mobility from the previous step's result
    patient_data_full['Mobility_Change'] = patient_data_full.groupby('Patient_ID')['Mobility'].diff()

    # 2. Get the Plan that was *actually used* to cause the change calculated above.
    # The Plan used at Step N (resulting in percepts at N) is the final plan the patient *received* at Step N-1.
    patient_data_full['Previous_Plan_Used_Intensity'] = patient_data_full.groupby('Patient_ID')[
        'Plan_Used_Intensity'].shift(1)

    # Use the cleaned patient data as the final trajectory data
    final_trajectory_data = patient_data_full.copy()

    # --- Dataframes required by app.py ---

    # 1. Model data (for macro trends 1 & 2)
    model_data = model.datacollector.get_model_vars_dataframe()

    # Raw agent data for time series plots (used by patient_data_rerun)
    raw_agent_data_rerun = model.datacollector.get_agent_vars_dataframe().reset_index()

    # 2. Patient data over time (for time series plots 5 & 6)
    # Filter only patient-related rows by checking for Mobility data
    patient_data_rerun = raw_agent_data_rerun[raw_agent_data_rerun['Mobility'].notna()].copy()

    # 3. Final step data for sampling (used for patient sampling in plots 5 & 6)
    final_step_patient_data_rerun = patient_data_rerun[patient_data_rerun['Step'] == max_days].copy()
    final_step_patient_data_rerun = final_step_patient_data_rerun.rename(columns={'AgentID': 'Patient_ID'})

    # 4. Final trajectory data (for plots 3, 4, and 7)
    return final_trajectory_data, model_data, patient_data_rerun, final_step_patient_data_rerun


# Running the function once to ensure execution environment consistency if needed,
# but main execution will be through Streamlit/app.py.
if __name__ == '__main__':
    final_trajectory_data, model_data, patient_data_rerun, final_step_patient_data_rerun = run_simulation_and_process_data()
    print("Simulation data processed successfully.")