import random
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.patient_repository import PatientRepository
from app.schemas.patient_schema import PatientDTO, EarDTO, AudiogramPointDTO
from app.models.enums import EarSideEnum, TestTypeEnum, PatientSourceEnum, HearingTypeEnum


class PatientGenerator:

    # Fallback templates if no real data is available in the database
    # These represent clinical "Exemplars"
    CLINICAL_TEMPLATES = [
        {
            "name": "Normal Hearing (Symmetrical)",
            "ears": {
                EarSideEnum.LEFT: {"AC": {250: 10, 500: 10, 1000: 10, 2000: 10, 4000: 10, 8000: 10}, "BC": {500: 10, 1000: 10, 2000: 10, 4000: 10}},
                EarSideEnum.RIGHT: {"AC": {250: 10, 500: 10, 1000: 10, 2000: 10, 4000: 10, 8000: 10}, "BC": {500: 10, 1000: 10, 2000: 10, 4000: 10}},
            }
        },
        {
            "name": "Presbycusis (Sloping SNHL)",
            "ears": {
                EarSideEnum.LEFT: {"AC": {250: 20, 500: 25, 1000: 30, 2000: 45, 4000: 60, 8000: 80}, "BC": {500: 25, 1000: 30, 2000: 45, 4000: 60}},
                EarSideEnum.RIGHT: {"AC": {250: 20, 500: 25, 1000: 30, 2000: 45, 4000: 65, 8000: 85}, "BC": {500: 25, 1000: 30, 2000: 45, 4000: 65}},
            }
        },
        {
            "name": "Noise-Induced Notch (4kHz)",
            "ears": {
                EarSideEnum.LEFT: {"AC": {250: 15, 500: 15, 1000: 15, 2000: 20, 4000: 55, 8000: 25}, "BC": {500: 15, 1000: 15, 2000: 20, 4000: 55}},
                EarSideEnum.RIGHT: {"AC": {250: 10, 500: 10, 1000: 15, 2000: 25, 4000: 60, 8000: 20}, "BC": {500: 10, 1000: 15, 2000: 25, 4000: 60}},
            }
        },
        {
            "name": "Conductive Loss (Otitis Media)",
            "ears": {
                EarSideEnum.LEFT: {"AC": {250: 45, 500: 40, 1000: 35, 2000: 30, 4000: 35, 8000: 40}, "BC": {500: 10, 1000: 10, 2000: 10, 4000: 10}},
                EarSideEnum.RIGHT: {"AC": {250: 40, 500: 35, 1000: 30, 2000: 25, 4000: 30, 8000: 35}, "BC": {500: 5, 1000: 5, 2000: 5, 4000: 5}},
            }
        }
    ]

    @staticmethod
    async def generate_patient(db: AsyncSession) -> int | None:
        """
        Generates a synthetic patient using Exemplar-Based Perturbed Sampling (EBPS).
        Uses real data from DB if available, otherwise falls back to clinical templates.
        """
        # 1. Selection: Try to get real patients (templates) from DB
        real_patients = await PatientRepository.get_profiles_by_source(db, PatientSourceEnum.REAL)

        if real_patients:
            # Joint Distribution: Pick an entire ear-pair (patient) from real data
            exemplar = random.choice(real_patients)
            patient_dto = await PatientGenerator._perturb_real_patient(exemplar)
        else:
            # Fallback to static clinical templates
            template = random.choice(PatientGenerator.CLINICAL_TEMPLATES)
            patient_dto = PatientGenerator._generate_from_template(template)

        # 2. Dynamic Masking Calculation
        # Based on Inter-aural Attenuation (IA) and Clinical Rules
        PatientGenerator._apply_masking_requirements(patient_dto)

        # 3. Save as a new SYNTHETIC patient
        patient_dto.source_type = PatientSourceEnum.SYNTHETIC
        saved_patient = await PatientRepository.save_patient(db, patient_dto)
        return saved_patient.id

    @staticmethod
    def _apply_masking_requirements(patient: PatientDTO):
        """Calculates and populates masking threshold placeholders."""
        INTER_AURAL_ATTENUATION = 40.0 # Standard for Headphones

        # Ear-to-ear comparison
        left_ear = next(e for e in patient.ears if e.side == EarSideEnum.LEFT)
        right_ear = next(e for e in patient.ears if e.side == EarSideEnum.RIGHT)

        for ear_under_test, opposite_ear in [(left_ear, right_ear), (right_ear, left_ear)]:
            new_points = []
            # Calculate AC Masking
            ac_points = [p for p in ear_under_test.audiogram_points if p.test_type == TestTypeEnum.AC]
            for ac_p in ac_points:
                # Rule: Mask if AC_TE - BC_NTE >= 40dB
                bc_nte_points = [p for p in opposite_ear.audiogram_points if p.test_type == TestTypeEnum.BC and p.frequency == ac_p.frequency]
                # Fallback to AC_NTE if BC_NTE is missing (assuming SNHL)
                if not bc_nte_points:
                    bc_nte_points = [p for p in opposite_ear.audiogram_points if p.test_type == TestTypeEnum.AC and p.frequency == ac_p.frequency]

                bc_nte_val = bc_nte_points[0].threshold_db if bc_nte_points else 0.0

                if (ac_p.threshold_db - bc_nte_val) >= INTER_AURAL_ATTENUATION:
                    # Target Masked Threshold: Simulate a slightly shifted masked threshold (+5-10dB)
                    new_points.append(AudiogramPointDTO(
                        test_type=TestTypeEnum.AC_MASKED,
                        frequency=ac_p.frequency,
                        threshold_db=ac_p.threshold_db + random.choice([0, 5])
                    ))

            # Calculate BC Masking
            bc_points = [p for p in ear_under_test.audiogram_points if p.test_type == TestTypeEnum.BC]
            for bc_p in bc_points:
                # Rule: Mask if ABG in TE > 10dB
                ac_te_val = next(p.threshold_db for p in ear_under_test.audiogram_points if p.test_type == TestTypeEnum.AC and p.frequency == bc_p.frequency)
                if (ac_te_val - bc_p.threshold_db) > 10.0:
                    new_points.append(AudiogramPointDTO(
                        test_type=TestTypeEnum.BC_MASKED,
                        frequency=bc_p.frequency,
                        threshold_db=bc_p.threshold_db + random.choice([0, 5])
                    ))

            ear_under_test.audiogram_points.extend(new_points)

    @staticmethod
    async def _perturb_real_patient(exemplar: PatientDTO) -> PatientDTO:
        """Applies controlled perturbation to a real patient exemplar."""
        shift = random.choice([-5, 0, 5])  # Global shift for this patient

        new_ears = []
        for ear in exemplar.ears:
            new_points = []
            # Calculate AC thresholds first as a reference for BC
            ac_map = {p.frequency: p.threshold_db for p in ear.audiogram_points if p.test_type == TestTypeEnum.AC}

            for p in ear.audiogram_points:
                # Local jitter ±5dB
                jitter = random.choice([-5, 0, 5])
                new_val = PatientGenerator._clamp(p.threshold_db + shift + jitter)

                # Clinical Constraint: BC cannot be worse than AC (allowing for small calibration error -5dB)
                if p.test_type == TestTypeEnum.BC:
                    ac_val = ac_map.get(p.frequency, new_val)
                    new_val = min(new_val, ac_val + 5)

                new_points.append(AudiogramPointDTO(
                    test_type=p.test_type,
                    frequency=p.frequency,
                    threshold_db=new_val
                ))

            new_ears.append(EarDTO(
                side=ear.side,
                hearing_type=ear.hearing_type,
                audiogram_points=new_points
            ))

        return PatientDTO(ears=new_ears)

    @staticmethod
    def _generate_from_template(template: dict) -> PatientDTO:
        """Generates a patient from a predefined clinical template."""
        shift = random.choice([-5, 0, 5])
        new_ears = []

        for side, tests in template["ears"].items():
            new_points = []
            # AC
            for freq, base_val in tests["AC"].items():
                val = PatientGenerator._clamp(base_val + shift + random.choice([-5, 0, 5]))
                new_points.append(AudiogramPointDTO(test_type=TestTypeEnum.AC, frequency=freq, threshold_db=val))
            # BC
            for freq, base_val in tests["BC"].items():
                ac_val = next(p.threshold_db for p in new_points if p.frequency == freq)
                val = PatientGenerator._clamp(base_val + shift + random.choice([-5, 0, 5]))
                val = min(val, ac_val) # Constraint
                new_points.append(AudiogramPointDTO(test_type=TestTypeEnum.BC, frequency=freq, threshold_db=val))

            new_ears.append(EarDTO(side=side, audiogram_points=new_points))

        return PatientDTO(ears=new_ears)

    @staticmethod
    def _clamp(val: float) -> float:
        """Clamps the threshold value to a realistic range and rounds to nearest 5dB."""
        val = max(-10, min(120, val))
        return round(val / 5) * 5
