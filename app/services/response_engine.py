from app.models.enums import ResponseEnum
from app.schemas.attempt_schema import AttemptCreateDTO


class ResponseEngine:

    @staticmethod
    def evaluate_tone(patient, attempt: AttemptCreateDTO):
        """
        Evaluates if a patient hears a tone based on their audiogram.
        """
        # 1. Find the correct ear
        target_ear = next((ear for ear in patient.ears if ear.side == attempt.ear_side), None)
        if not target_ear:
            return ResponseEnum.NOT_HEARD

        # 2. Find the threshold for the given test type and frequency
        # Note: If test_type is masked (AC_masked, BC_masked), we currently use the base (AC, BC)
        # unless specific masked thresholds are stored.
        base_test_type = attempt.test_type
        if base_test_type == "AC_masked": base_test_type = "AC"
        if base_test_type == "BC_masked": base_test_type = "BC"

        point = next((
            p for p in target_ear.audiogram_points
            if p.test_type == attempt.test_type and p.frequency == attempt.frequency
        ), None)

        # Fallback to base test type if masked not found
        if not point and attempt.test_type != base_test_type:
             point = next((
                p for p in target_ear.audiogram_points
                if p.test_type == base_test_type and p.frequency == attempt.frequency
            ), None)

        if not point:
            # If no point is found for this frequency, assume they can't hear it (or default to a very high threshold)
            return ResponseEnum.NOT_HEARD

        # 3. Compare intensity with threshold
        if attempt.intensity >= point.threshold_db:
            return ResponseEnum.HEARD

        return ResponseEnum.NOT_HEARD