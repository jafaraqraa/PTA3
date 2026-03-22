from app.models.enums import ResponseEnum
from app.schemas.attempt_schema import AttemptCreateDTO


class ResponseEngine:

    @staticmethod
    def evaluate_tone(patient, attempt: AttemptCreateDTO):

        # منطق مبسط حالياً
        if attempt.intensity >= 40:
            return ResponseEnum.HEARD

        return ResponseEnum.NOT_HEARD