from mesa import Agent

class PhysicianAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.intervention_count = 0
        self.patients_under_review = {}  # Data from CareAgents for review

    def receive_review_data(self, data):
        """Receives review data from all assigned Care Agents."""
        self.patients_under_review[data['patient_id']] = data

    def step(self):
        """MAS Requirement: Provide Guidance and Make Treatment Decisions (Override logic)."""

        final_plans = {}
        for patient_id, data in self.patients_under_review.items():

            care_plan = data['care_plan']

            # --- Physician Intervention Logic ---

            # Scenario: High-Risk Alert
            # If the CareAgent flagged an alert AND the patient's BP is critically high, the physician intervenes.
            if data['alert_flag'] and data['current_bp'] > 145:
                # Override: Max out medication and force rest
                care_plan['exercise_intensity'] = 1
                care_plan['medication_dosage'] = 10
                self.intervention_count += 1
                # print(f"Physician Agent {self.unique_id} INTERVENED for Patient {patient_id}: High BP ({data['current_bp']:.1f}).")

            # Scenario: High Pain/Low Intensity Mismatch
            # If pain is high (7+) but the CareAgent suggested progression, the physician forces a maintenance plan.
            elif data['current_pain'] >= 7 and care_plan['exercise_intensity'] > 2:
                care_plan['exercise_intensity'] = 2  # Force low intensity
                self.intervention_count += 1

            # --- End Intervention Logic ---

            final_plans[patient_id] = care_plan

        self.patients_under_review = {}  # Clear data for the next step
        return final_plans  # Return final plans for all patients