from mesa import Agent

class CareAgent(Agent):
    def __init__(self, unique_id, model, patient_id, physician_id):
        super().__init__(unique_id, model)
        self.patient_id = patient_id
        self.physician_id = physician_id
        self.percept_history = []
        self.current_care_plan = {"exercise_intensity": 1, "medication_dosage": 5, "temperature_management": False}
        self.alert_status = False

    def perceive(self, patient_state):
        """Stores the patient's current state (percept)."""
        self.percept_history.append(patient_state)
        if len(self.percept_history) > 3: self.percept_history.pop(0)

    def step(self):
        """Applies Rule-Based Logic to adjust the care plan (Action) and checks for ALERTS."""
        if not self.percept_history:
            return self.current_care_plan, False  # Plan, Alert_Flag

        latest_state = self.percept_history[-1]
        new_intensity = self.current_care_plan["exercise_intensity"]
        new_dosage = self.current_care_plan["medication_dosage"]
        new_temp_management = self.current_care_plan.get("temperature_management", False)

        # --- MAS Requirement: Real-time Monitoring & Alert Logic ---
        alert_flag = False
        if latest_state["pain"] >= 8.5 or latest_state.get("bp", 120) > 135 or latest_state.get("body_temp",
                                                                                                37.0) > 38.0:
            alert_flag = True
        self.alert_status = alert_flag  # Internal tracking

        # Base adjustments based on comorbidity score
        max_intensity_adjusted = max(1, 5 - latest_state.get("comorbidity_score", 0))
        min_dosage_adjusted = max(1, 1 + latest_state.get("comorbidity_score", 0))

        # Rule 1: Emergency/Setback (Higher-level monitoring logic)
        if latest_state["complication"] or latest_state["pain"] >= 9 or latest_state.get("bp",
                                                                                         120) > 140 or latest_state.get(
                "body_temp", 37.0) > 38.5:
            new_intensity = 1
            new_dosage = min(10, new_dosage + 3)
            new_temp_management = True

        # Rule 2: Progression Check
        elif len(self.percept_history) >= 2:
            consistent_progress = all(
                p.get("mobility", 0) > 6 and p.get("pain", 10) < 5 and p.get("bp", 150) < 130 and p.get("body_temp",
                                                                                                        39.0) < 37.8 for
                p in self.percept_history[-2:])

            if consistent_progress and new_intensity < max_intensity_adjusted:
                new_intensity += 1
                if latest_state.get("pain", 10) < 4 and latest_state.get("bp",
                                                                         150) < 125 and new_dosage > min_dosage_adjusted:
                    new_dosage = max(min_dosage_adjusted, new_dosage - 1)
                if latest_state.get("body_temp", 37.0) < 37.6:
                    new_temp_management = False

        # Rule 3: Plateau Detection
        elif latest_state.get("mobility", 0) < 8 and new_intensity > 1:
            if len(self.percept_history) >= 3:
                mobility_change = self.percept_history[-1].get("mobility", 0) - self.percept_history[0].get("mobility",
                                                                                                            0)
                bp_change = latest_state.get("bp", 120) - self.percept_history[0].get("bp", 120)

                if mobility_change < 0.1 and bp_change > -0.1:
                    new_intensity = max(1, new_intensity - 1)

        # Clamp exercise intensity and dosage
        new_intensity = min(new_intensity, max_intensity_adjusted)
        new_dosage = max(new_dosage, min_dosage_adjusted)

        # Update and return the new plan and alert status
        self.current_care_plan = {
            "exercise_intensity": new_intensity,
            "medication_dosage": new_dosage,
            "temperature_management": new_temp_management
        }

        # Pass the plan and the current high-risk state for the physician's review
        physician_review_data = {
            'patient_id': self.patient_id,
            'care_plan': self.current_care_plan,
            'alert_flag': alert_flag,
            'current_bp': latest_state.get("bp"),
            'current_temp': latest_state.get("body_temp"),
            'current_pain': latest_state.get("pain")
        }

        return physician_review_data
