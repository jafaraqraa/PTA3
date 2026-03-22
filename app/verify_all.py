
import asyncio
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.patient_generator import PatientGenerator
from app.services.response_engine import ResponseEngine
from app.schemas.attempt_schema import AttemptCreateDTO
from app.models.enums import EarSideEnum, TestTypeEnum, ResponseEnum

async def test_generator_and_response():
    print("Testing Patient Generator...")
    db = MagicMock(spec=AsyncSession)

    # Mocking PatientRepository
    from app.repositories.patient_repository import PatientRepository
    from app.schemas.patient_schema import PatientDTO

    # Mock save_patient
    async def mock_save_patient(db, dto):
        dto.id = 1
        return dto
    PatientRepository.save_patient = mock_save_patient

    # Mock get_real_patients to return empty list (trigger fallback)
    PatientRepository.get_real_patients = MagicMock(return_value=asyncio.Future())
    PatientRepository.get_real_patients.return_value.set_result([])

    # Generate multiple patients to check for variance and profile selection
    for i in range(3):
        patient_id = await PatientGenerator.generate_patient(db)
        print(f"Generated patient {i+1} with ID: {patient_id}")

    # Test Response Engine with a manual patient
    print("\nTesting Response Engine...")
    from app.schemas.patient_schema import EarDTO, AudiogramPointDTO

    mock_patient = MagicMock()
    left_ear = MagicMock()
    left_ear.side = EarSideEnum.LEFT
    left_ear.audiogram_points = [
        AudiogramPointDTO(test_type=TestTypeEnum.AC, frequency=1000, threshold_db=25.0)
    ]
    mock_patient.ears = [left_ear]

    # Tone at 30dB (Should be HEARD)
    attempt_heard = AttemptCreateDTO(
        session_id=1, ear_side=EarSideEnum.LEFT, test_type=TestTypeEnum.AC, frequency=1000, intensity=30.0
    )
    res_heard = ResponseEngine.evaluate_tone(mock_patient, attempt_heard)
    print(f"Tone at 30dB (threshold 25dB): {res_heard}")

    # Tone at 20dB (Should be NOT_HEARD)
    attempt_not_heard = AttemptCreateDTO(
        session_id=1, ear_side=EarSideEnum.LEFT, test_type=TestTypeEnum.AC, frequency=1000, intensity=20.0
    )
    res_not_heard = ResponseEngine.evaluate_tone(mock_patient, attempt_not_heard)
    print(f"Tone at 20dB (threshold 25dB): {res_not_heard}")

    assert res_heard == ResponseEnum.HEARD
    assert res_not_heard == ResponseEnum.NOT_HEARD
    print("\nSuccess! Generator and Response Engine working as expected.")

if __name__ == "__main__":
    asyncio.run(test_generator_and_response())
