import random
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.patient_repository import PatientRepository
from app.schemas.patient_schema import PatientDTO, EarDTO, AudiogramPointDTO
from app.models.enums import EarSideEnum, TestTypeEnum, PatientSourceEnum, HearingTypeEnum


class PatientGenerator:

    # Fallback profiles when no 'REAL' source patients are available
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
        """
        Generates a virtual patient using Exemplar-Based Perturbed Sampling (EBPS).
        Falls back to template-based generation if no 'REAL' patients are found.
        """
        real_patients = await PatientRepository.get_real_patients(db)

        if real_patients:
            # EBPS: Sample and perturb a real ear-pair
            base_patient = random.choice(real_patients)
            new_patient = PatientGenerator._ebps_perturb(base_patient)
        else:
            # Fallback to templates
            new_patient = PatientGenerator._generate_from_template()

        saved_patient = await PatientRepository.save_patient(db, new_patient)
        return saved_patient.id

    @staticmethod
    def _ebps_perturb(base_patient) -> PatientDTO:
        """Applies jitter and clinical constraints to a real patient template."""
        jitter_base = random.choice([-5, 0, 5])

        ears_dto = []
        for base_ear in base_patient.ears:
            new_points = []

            # Map existing points to facilitate BC <= AC check
            ac_map = {p.frequency: p.threshold_db for p in base_ear.audiogram_points if p.test_type in [TestTypeEnum.AC, TestTypeEnum.AC_MASKED]}
            bc_map = {p.frequency: p.threshold_db for p in base_ear.audiogram_points if p.test_type in [TestTypeEnum.BC, TestTypeEnum.BC_MASKED]}

            for p in base_ear.audiogram_points:
                # Apply base jitter
                val = p.threshold_db + jitter_base

                # Apply clinical constraints
                if p.test_type in [TestTypeEnum.AC, TestTypeEnum.AC_MASKED]:
                    # Ensure BC <= AC
                    if p.frequency in bc_map:
                        val = max(val, bc_map[p.frequency] + jitter_base)

                if p.test_type in [TestTypeEnum.BC, TestTypeEnum.BC_MASKED]:
                    # Ensure BC <= AC
                    if p.frequency in ac_map:
                        val = min(val, ac_map[p.frequency] + jitter_base)

                val = max(-10, min(120, val))
                val = round(val / 5) * 5 # Ensure 5dB steps

                new_points.append(AudiogramPointDTO(
                    test_type=p.test_type,
                    frequency=p.frequency,
                    threshold_db=val
                ))

            ears_dto.append(EarDTO(
                side=base_ear.side,
                hearing_type=base_ear.hearing_type,
                audiogram_points=new_points
            ))

        return PatientDTO(
            source_type=PatientSourceEnum.SYNTHETIC,
            ears=ears_dto
        )

    @staticmethod
    def _generate_from_template() -> PatientDTO:
        """Generates a patient from hardcoded clinical templates."""
        profile_name = random.choice(list(PatientGenerator.HEARING_PROFILES.keys()))
        profile = PatientGenerator.HEARING_PROFILES[profile_name]

        def add_variance(value: float) -> float:
            variance = random.choice([-5, 0, 5])
            return max(-10, min(120, value + variance))

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

        return PatientDTO(
            source_type=PatientSourceEnum.SYNTHETIC,
            ears=[left_ear, right_ear]
        )
