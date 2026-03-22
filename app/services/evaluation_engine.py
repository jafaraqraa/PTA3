from app.models.enums import ResponseEnum
from app.schemas.session_schema import SessionFullDTO


class EvaluationEngine:

    @staticmethod
    def evaluate_session(session: SessionFullDTO):
        # وصول مباشر لكل الداتا
        patient = session.patient
        attempts = session.attempts
        stored = session.stored_thresholds

        # مثال استخدام بيانات المريض
        ears = patient.ears if patient else []
        left_ear = next((e for e in ears if e.side == "LEFT"), None)

        # مثال حساب بسيط
        heard = sum(1 for a in attempts if a.response == ResponseEnum.HEARD)
        total = len(attempts)

        return {
            "start_time": session.start_time,
            "end_time": session.end_time,
            "heard": heard,
            "total": total,
            "stored_thresholds": len(stored)
        }

