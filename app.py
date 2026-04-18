import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import random

# Assuming run.py is in the same directory and contains the function
from run import run_simulation_and_process_data

# --- Configuration ---
st.set_page_config(layout="wide", page_title="Post-Op Care MAS Simulation Dashboard")

# PATIENT_ID_TO_TRACK is no longer imported from run.py, use a default value
PATIENT_ID_TO_TRACK = 0


# --- Data Caching and Simulation Run ---
@st.cache_data
def get_data(num_patients, max_days):
    """Caches the simulation run result to prevent re-running the heavy simulation."""
    st.write(f"Running simulation for **{num_patients}** patients over **{max_days}** days...")
    return run_simulation_and_process_data(num_patients, max_days)


# --- Sidebar Controls ---
st.sidebar.header("Simulation Controls")
NUM_PATIENTS = st.sidebar.slider("Number of Patients", 10, 500, 100)
MAX_DAYS = st.sidebar.slider("Simulation Length (Days)", 10, 120, 60)

# Run simulation and get data (cached)
final_trajectory_data, model_data, patient_data_rerun, final_step_patient_data_rerun = get_data(NUM_PATIENTS, MAX_DAYS)

# Get list of valid Patient IDs for selection
patient_ids = sorted(final_trajectory_data['Patient_ID'].unique().tolist())


# --- Plotting Functions ---

def plot_macro_trends(model_data, final_trajectory_data):
    """Generates all macro and group plots (1-6) on the Dashboard tab."""

    st.header("Overall Model & Group Analysis")

    # Row 1: Macro Trends (Plots 1 & 2)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Average Mobility Over Time")
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(model_data.index, model_data['Average_Mobility'])
        ax.set_xlabel("Step (Day)")
        ax.set_ylabel("Average Mobility Score")
        ax.set_title("Average Patient Mobility Over Time")
        ax.grid(True)
        st.pyplot(fig)

    with col2:
        st.subheader("2. Physician Intervention Count")
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(model_data.index, model_data['Physician_Intervention_Count'], color='tab:orange')
        ax.set_xlabel("Step (Day)")
        ax.set_ylabel("Cumulative Interventions")
        ax.set_title("Physician Agent Interventions Over Time")
        ax.grid(True)
        st.pyplot(fig)

    st.markdown("---")

    # Row 2: Group Mechanisms (Plots 3 & 4)
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("3. Impact of Exercise Intensity on Mobility Change")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.boxplot(
            x='Previous_Plan_Used_Intensity',
            y='Mobility_Change',
            data=final_trajectory_data.dropna(subset=['Previous_Plan_Used_Intensity', 'Mobility_Change']),
            ax=ax
        )
        ax.set_xlabel("Previous Plan Used Intensity")
        ax.set_ylabel("Change in Mobility")
        ax.set_title("Impact of Exercise Intensity on Mobility Change")
        st.pyplot(fig)

    with col4:
        st.subheader("4. Agent Response: BP vs. Medication Dosage")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.scatterplot(
            x='BP',
            y='Plan_Used_Medication',
            data=final_trajectory_data[final_trajectory_data['BP'] > 120],
            ax=ax
        )
        ax.set_xlabel("Blood Pressure (Patient Percept)")
        ax.set_ylabel("FINAL Medication Dosage (Agent Action)")
        ax.set_title("Agent Response: BP vs. FINAL Medication Dosage (BP > 120)")
        st.pyplot(fig)

    st.markdown("---")

    # Row 3: Time Series Trends (Plots 5 & 6)

    st.subheader("5 & 6. Trends for Sampled Patients")

    # --- CRITICAL FIX: Ensure only valid Patient IDs are sampled (even numbers) ---
    all_agent_ids = patient_data_rerun['AgentID'].unique()

    # Filter for valid Patient IDs (even numbers, as CareAgents are odd, and Physician is 9999)
    valid_patient_ids = [int(p) for p in all_agent_ids if int(p) % 2 == 0]
    population_size = len(valid_patient_ids)

    if population_size == 0:
        selected_patient_ids = []
    elif population_size < 5:
        # If fewer than 5 patients, select all available
        selected_patient_ids = valid_patient_ids
    else:
        num_patients_to_sample = 5
        # Randomly sample 5 IDs from the list of valid patient IDs
        selected_patient_ids = random.sample(valid_patient_ids, num_patients_to_sample)

    # --- END FIX ---

    if not selected_patient_ids:
        st.warning(
            "Not enough valid patient data found to sample patients for time series plots. Please check simulation parameters.")
        return  # Exit the function if no IDs are selected

    # Create subplots for time series
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))

    # Plot 5: Blood Pressure over time
    for patient_id in selected_patient_ids:
        # Filter using AgentID column from patient_data_rerun
        patient_trajectory = patient_data_rerun[patient_data_rerun['AgentID'] == patient_id]
        if not patient_trajectory.empty:
            axes[0].plot(patient_trajectory['Step'], patient_trajectory['BP'], label=f'Patient {int(patient_id)}')

    axes[0].set_xlabel("Step (Day)")
    axes[0].set_ylabel("Blood Pressure")
    axes[0].set_title("5. Blood Pressure Over Time for Selected Patients")
    axes[0].legend(loc='upper right', bbox_to_anchor=(1.25, 1))
    axes[0].grid(True)

    # Plot 6: Body Temperature over time
    for patient_id in selected_patient_ids:
        # Filter using AgentID column from patient_data_rerun
        patient_trajectory = patient_data_rerun[patient_data_rerun['AgentID'] == patient_id]
        if not patient_trajectory.empty:
            axes[1].plot(patient_trajectory['Step'], patient_trajectory['Body_Temp'],
                         label=f'Patient {int(patient_id)}')

    axes[1].set_xlabel("Step (Day)")
    axes[1].set_ylabel("Body Temperature (°C)")
    axes[1].set_title("6. Body Temperature Over Time for Selected Patients")
    axes[1].legend(loc='upper right', bbox_to_anchor=(1.25, 1))
    axes[1].grid(True)

    plt.tight_layout(rect=[0, 0, 0.9, 1])
    st.pyplot(fig)


def plot_patient_trajectory(patient_id, final_trajectory_data, max_days):
    """Generates the single patient trajectory plot (Plot 7)."""

    patient_trajectory = final_trajectory_data[final_trajectory_data['Patient_ID'] == patient_id].copy()

    if patient_trajectory.empty:
        st.warning(f"Data not available for Patient ID {patient_id}.")
        return

    st.header(f"Patient {int(patient_id)} Trajectory (Plot 7)")

    # State Summary
    initial_condition = patient_trajectory.iloc[0]

    # Determine the actual final step
    final_step_day = int(patient_trajectory.iloc[-1]['Step'])
    final_condition = patient_trajectory.iloc[-1]

    # If the simulation ran less than MAX_DAYS, use the final step day for display
    display_max_day = min(max_days, final_step_day)

    st.subheader("Patient Condition Summary")
    colA, colB = st.columns(2)

    with colA:
        st.metric("Initial Mobility (Day 0)", f"{initial_condition['Mobility']:.2f}")
        st.metric("Initial Pain (Day 0)", f"{initial_condition['Pain']:.1f}")
    with colB:
        # Correctly use the display_max_day variable in the f-string
        st.metric(f"Final Mobility (Day {display_max_day})", f"{final_condition['Mobility']:.2f}")
        st.metric(f"Final Pain (Day {display_max_day})", f"{final_condition['Pain']:.1f}")

    # Plot 7: Trajectory
    st.subheader("Mobility, Pain, and Final Plan Over Time")

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot Mobility and Pain on the first y-axis
    ax1.plot(patient_trajectory['Step'], patient_trajectory['Mobility'], label='Mobility Score', color='tab:blue')
    ax1.plot(patient_trajectory['Step'], patient_trajectory['Pain'], label='Pain Level', color='tab:red')
    ax1.set_xlabel("Step (Day)")
    ax1.set_ylabel("Patient State (1-10)", color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.grid(True)

    # Create a second y-axis for Suggested Plan (Intensity and Medication)
    ax2 = ax1.twinx()
    ax2.plot(patient_trajectory['Step'], patient_trajectory['Plan_Used_Intensity'], label='FINAL Exercise Intensity',
             color='tab:green', linestyle='-')
    ax2.plot(patient_trajectory['Step'], patient_trajectory['Plan_Used_Medication'], label='FINAL Medication Dosage',
             color='tab:purple', linestyle='--')
    ax2.set_ylabel("FINAL Plan Value", color="tab:green")
    ax2.tick_params(axis='y', labelcolor='tab:green')

    # Add title and legend
    plt.title(f"Patient {int(patient_id)}: State vs. Final Agent Actions Over Time (MAS)")
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))

    st.pyplot(fig)


# --- Main Application Layout (Tabs) ---

st.title("Post-Operative Care Multi-Agent System (MAS) Simulation")

tab_dashboard, tab_patient = st.tabs(["📊 Simulation Dashboard (Plots 1-6)", "🔬 Patient Trajectory (Plot 7)"])

with tab_dashboard:
    plot_macro_trends(model_data, final_trajectory_data)

with tab_patient:
    if not patient_ids:
        st.error("No patient data found. Check your simulation run and data processing in run.py.")
    else:
        st.subheader("Select Patient ID")

        # Set default index for selectbox
        try:
            default_index = patient_ids.index(PATIENT_ID_TO_TRACK)
        except ValueError:
            default_index = 0

        # User selection for Patient ID
        selected_patient_id = st.selectbox(
            "Choose a Patient ID (even numbers correspond to patients):",
            options=patient_ids,
            index=default_index
        )

        plot_patient_trajectory(selected_patient_id, final_trajectory_data, MAX_DAYS)

st.sidebar.markdown(f"---")
st.sidebar.info("Adjust the controls above and click 'Rerun' to run a new simulation.")