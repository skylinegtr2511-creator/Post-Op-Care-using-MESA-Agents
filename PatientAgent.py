from mesa import Agent
import random
import pandas as pd

file_path = 'patient-data.csv'
df = pd.read_csv(file_path)

class PatientAgent(Agent):
    def __init__(self, unique_id, model, initial_age, recovery_type, adherence_likelihood,
                 bp, body_temp, comorbidity_score):
        super().__init__(unique_id, model)
        self.age = initial_age
        self.recovery_type = recovery_type
        self.adherence_likelihood = adherence_likelihood

        # Dynamic State Variables (Percepts)
        self.current_day = 0
        self.mobility_score = 3.0
        self.pain_level = 7.0
        self.complication_status = False

        # Static/New attributes
        self.bp = bp
        self.body_temp = body_temp
        self.comorbidity_score = comorbidity_score

        # Initial Plan setup
        random_plan = df.sample(1).iloc[0]
        self.current_plan = {
            "exercise_intensity": int(random_plan["EXERCISE_INTENSITY"]),
            "medication_dosage": int(random_plan["MEDICATION_DOSAGE"]),
            "temperature_management": bool(random_plan["TEMPERATURE_MANAGEMENT"])
        }

    def receive_plan(self, new_plan):
        """Updates the care plan for the next day's actions."""
        # This is the FINAL plan after CareAgent and PhysicianAgent review
        self.current_plan = new_plan

    def step(self):
        """The agent's action for one time step (one day)."""
        self.current_day += 1

        # 1. Adherence Check
        adheres = random.random() < self.adherence_likelihood

        # 2. State Update (Dynamics - Retained from previous code)
        if adheres:
            recovery_bonus = 0.1 if self.recovery_type == 'High' else (-0.1 if self.recovery_type == 'Low' else 0.0)
            improvement = (self.current_plan["exercise_intensity"] * 0.15) + recovery_bonus * (10 - self.mobility_score) / 10
            self.mobility_score = min(10.0, self.mobility_score + improvement)

            pain_reduction = self.current_plan["medication_dosage"] * 0.05
            self.pain_level = max(1.0, self.pain_level - pain_reduction)
        else:
            self.mobility_score = max(1.0, self.mobility_score - 0.2)
            self.pain_level = min(10.0, self.pain_level + 0.5)

        # Update BP/Body Temp based on state and plan
        bp_change = 0
        if self.pain_level > 7: bp_change += 0.5
        if self.complication_status: bp_change += 1.0
        bp_change -= self.current_plan["medication_dosage"] * 0.1 * adheres
        self.bp = max(90.0, min(160.0, self.bp + bp_change + random.uniform(-0.5, 0.5)))

        temp_change = 0
        if self.complication_status: temp_change += 0.2
        if self.current_plan.get("temperature_management", False) and adheres: temp_change -= 0.3
        self.body_temp = min(40.0, self.body_temp + temp_change + random.uniform(-0.1, 0.1))

        # 3. Complication Check
        base_risk = 0.01
        pain_factor = self.pain_level / 10
        comorbidity_factor = self.comorbidity_score * 0.005
        bp_factor = (self.bp - 120) / 100
        temp_factor = (self.body_temp - 37.0) / 5

        risk_score = (base_risk + pain_factor * 0.03 + comorbidity_factor + bp_factor * 0.01 + temp_factor * 0.02)
        if random.random() < risk_score:
            self.complication_status = True

        # Return the current state (Percept) for the Care Agent
        return {
            "id": self.unique_id,
            "mobility": self.mobility_score,
            "pain": self.pain_level,
            "complication": self.complication_status,
            "bp": self.bp,
            "body_temp": self.body_temp,
            "comorbidity_score": self.comorbidity_score,
            "risk_score": risk_score
        }
