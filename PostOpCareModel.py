from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
import random
from PatientAgent import PatientAgent
from CareAgent import CareAgent
from PhysicianAgent import PhysicianAgent
import pandas as pd

file_path = 'patient-data.csv'
df = pd.read_csv(file_path)

# --- Helper Functions for DataCollector (Unchanged) ---
def get_average_mobility(model):
    mobilities = [agent.mobility_score for agent in model.schedule.agents if isinstance(agent, PatientAgent)]
    return sum(mobilities) / len(mobilities) if mobilities else 0


def get_complication_count(model):
    return sum(1 for agent in model.schedule.agents if isinstance(agent, PatientAgent) and agent.complication_status)


def get_physician_interventions(model):
    return sum(agent.intervention_count for agent in model.schedule.agents if isinstance(agent, PhysicianAgent))


# --- PostOpCareModel Definition (Updated for Physician MAS) ---
class PostOpCareModel(Model):
    def __init__(self, num_patients=100, max_steps=60):
        self.num_patients = num_patients
        self.running = True
        self.max_steps = max_steps
        self.schedule = SimultaneousActivation(self)
        self.patient_care_map = {}

        # MAS Component 1: Physician Agent
        # Use a single Physician Agent to review all Care Agent decisions
        physician_agent = PhysicianAgent(9999, self)
        self.schedule.add(physician_agent)

        # Initialize Patient and Care Agents
        for i in range(self.num_patients):
            patient_id = i * 2
            care_id = i * 2 + 1

            # Patient Agent setup
            age = random.randint(30, 80)
            recovery_type = random.choice(['High', 'Average', 'Low'])
            adherence = random.uniform(0.5, 0.95)
            initial_bp = random.uniform(110.0, 130.0)
            initial_body_temp = random.uniform(36.5, 37.5)
            initial_comorbidity_score = random.randint(0, 5)

            patient_agent = PatientAgent(patient_id, self, age, recovery_type, adherence, initial_bp, initial_body_temp,
                                         initial_comorbidity_score)
            self.schedule.add(patient_agent)

            # Care Agent setup
            # Link Care Agent to the Physician Agent ID
            care_agent = CareAgent(care_id, self, patient_id, physician_agent.unique_id)
            self.schedule.add(care_agent)

            self.patient_care_map[patient_id] = {'care': care_agent, 'patient': patient_agent,
                                                 'physician': physician_agent}

        # Setup Data Collector
        self.datacollector = DataCollector(
            model_reporters={
                "Average_Mobility": get_average_mobility,
                "Complication_Count": get_complication_count,
                "Physician_Intervention_Count": get_physician_interventions
            },
            agent_reporters={
                # Patient State Percepts
                "Day": lambda a: a.current_day if isinstance(a, PatientAgent) else None,
                "Mobility": lambda a: a.mobility_score if isinstance(a, PatientAgent) else None,
                "Pain": lambda a: a.pain_level if isinstance(a, PatientAgent) else None,
                "BP": lambda a: a.bp if isinstance(a, PatientAgent) else None,
                "Body_Temp": lambda a: a.body_temp if isinstance(a, PatientAgent) else None,
                "Comorbidity_Score": lambda a: a.comorbidity_score if isinstance(a, PatientAgent) else None,
                "Complication": lambda a: a.complication_status if isinstance(a, PatientAgent) else None,

                # Plan Used by Patient (from previous step's decision)
                "Plan_Used_Intensity": lambda a: a.current_plan["exercise_intensity"] if isinstance(a,
                                                                                                    PatientAgent) else None,
                "Plan_Used_Medication": lambda a: a.current_plan["medication_dosage"] if isinstance(a,
                                                                                                    PatientAgent) else None,

                # Care Agent's internal decision (before Physician review)
                "CA_Suggested_Intensity": lambda a: a.current_care_plan["exercise_intensity"] if isinstance(a,
                                                                                                            CareAgent) else None,
                "CA_Suggested_Medication": lambda a: a.current_care_plan["medication_dosage"] if isinstance(a,
                                                                                                            CareAgent) else None,
                "CA_Alert_Status": lambda a: a.alert_status if isinstance(a, CareAgent) else None,
            }
        )

        # Collect the initial state (Step 0)
        self.datacollector.collect(self)

    def step(self):
        """MAS: Patient step -> Care Agent step -> Physician Agent step -> Patient receives final plan."""

        # --- 1. Patient Step & Care Agent Perception ---
        # Patient agents execute actions and return their percepts.
        # Care agents perceive those percepts and make an initial decision/alert.
        physician_review_queue = {}
        for agent_id, agent_pair in self.patient_care_map.items():
            patient = agent_pair['patient']
            care = agent_pair['care']

            # Patient acts, returns percept
            percept = patient.step()

            # Care Agent perceives, makes a plan, and flags review data/alerts
            care.perceive(percept)
            review_data = care.step()  # returns physician_review_data

            # Send data to the Physician Agent's review queue
            physician_review_queue[agent_id] = review_data

        # --- 2. Physician Agent Intervention ---
        # A single physician agent receives all review data and decides on final plans.
        physician_agent = self.schedule.agents[0]  # Assuming PhysicianAgent is the first (ID 9999)

        for patient_id, data in physician_review_queue.items():
            physician_agent.receive_review_data(data)

        final_plans = physician_agent.step()

        # --- 3. Patients Receive Final Plan ---
        for patient_id, final_plan in final_plans.items():
            patient = self.patient_care_map[patient_id]['patient']
            patient.receive_plan(final_plan)

        # Collect data and check termination condition
        self.datacollector.collect(self)
        self.schedule.step()

        if self.schedule.steps >= self.max_steps:
            self.running = False