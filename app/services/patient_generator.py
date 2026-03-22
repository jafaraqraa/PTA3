import random
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.patient_repository import PatientRepository
from app.schemas.patient_schema import PatientDTO, EarDTO, AudiogramPointDTO
from app.models.enums import EarSideEnum, TestTypeEnum, PatientSourceEnum, HearingTypeEnum


class PatientGenerator:

    # Hearing profile templates with base AC and BC thresholds
    HEARING_PROFILES = {
        "Normal": {
            "hearing_type": HearingTypeEnum.NORMAL,
            "ac": {
                125: 5, 250: 5, 500: 5, 750: 5, 1000: 5, 1500: 5,
                2000: 5, 3000: 5, 4000: 5, 6000: 5, 8000: 5
            },
            "bc": {
                500: 5, 750: 5, 1000: 5, 1500: 5, 2000: 5, 3000: 5, 4000: 5
            }
        },
        "Presbycusis": {
            "hearing_type": HearingTypeEnum.SENSORINEURAL,
            "ac": {
                125: 10, 250: 10, 500: 15, 750: 20, 1000: 25, 1500: 35,
                2000: 45, 3000: 55, 4000: 65, 6000: 75, 8000: 85
            },
            "bc": {
                500: 15, 750: 20, 1000: 25, 1500: 35, 2000: 45, 3000: 55, 4000: 65
            }
        },
        "NoiseInduced": {
            "hearing_type": HearingTypeEnum.SENSORINEURAL,
            "ac": {
                125: 10, 250: 10, 500: 10, 750: 10, 1000: 15, 1500: 20,
                2000: 30, 3000: 50, 4000: 70, 6000: 40, 8000: 20
            },
            "bc": {
                500: 10, 750: 10, 1000: 15, 1500: 20, 2000: 30, 3000: 50, 4000: 70
            }
        },
        "FlatSNHL": {
            "hearing_type": HearingTypeEnum.SENSORINEURAL,
            "ac": {
                125: 40, 250: 40, 500: 40, 750: 40, 1000: 40, 1500: 40,
                2000: 40, 3000: 40, 4000: 40, 6000: 40, 8000: 40
            },
            "bc": {
                500: 40, 750: 40, 1000: 40, 1500: 40, 2000: 40, 3000: 40, 4000: 40
            }
        }
    }

    @staticmethod
    async def generate_patient(db: AsyncSession) -> int | None:

        def add_variance(value: float) -> float:
            """Adds a random variance of [-5, 0, 5] dB."""
            variance = random.choice([-5, 0, 5])
            return max(-10, min(120, value + variance))

        # Randomly select a profile
        profile_name = random.choice(list(PatientGenerator.HEARING_PROFILES.keys()))
        profile = PatientGenerator.HEARING_PROFILES[profile_name]

        def build_points(ac_base: dict, bc_base: dict) -> list[AudiogramPointDTO]:
            points = []
            for freq, threshold in ac_base.items():
                points.append(AudiogramPointDTO(
                    test_type=TestTypeEnum.AC,
                    frequency=freq,
                    threshold_db=add_variance(threshold)
                ))
            for freq, threshold in bc_base.items():
                points.append(AudiogramPointDTO(
                    test_type=TestTypeEnum.BC,
                    frequency=freq,
                    threshold_db=add_variance(threshold)
                ))
            return points

        left_ear = EarDTO(
            side=EarSideEnum.LEFT,
            hearing_type=profile["hearing_type"],
            audiogram_points=build_points(profile["ac"], profile["bc"])
        )

        right_ear = EarDTO(
            side=EarSideEnum.RIGHT,
            hearing_type=profile["hearing_type"],
            audiogram_points=build_points(profile["ac"], profile["bc"])
        )

        new_patient = PatientDTO(
            source_type=PatientSourceEnum.SYNTHETIC,
            ears=[left_ear, right_ear]
        )

        saved_patient = await PatientRepository.save_patient(db, new_patient)
        return saved_patient.id
