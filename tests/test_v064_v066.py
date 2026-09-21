"""Independent reference tests for the 0.6.4-0.6.6 engineering chain."""

import math

import numpy as np
import pytest

from kincheckapi.dynamics import (
    DampingSpec,
    ElasticMaterial,
    FatigueMaterial,
    MeanStressCorrection,
    ModalRequest,
    ScenarioMatrix,
    StressHistory,
    StructuralLoad,
    StructuralModel,
    check_fatigue_limits,
    check_resonance_margin,
    check_stress,
    compute_rms,
    estimate_psd,
    evaluate_fatigue,
    evaluate_operating_envelope,
    solve_frequency_response,
    solve_modes,
    solve_static_structure,
    solve_transient_response,
    summarize_drive_duty,
)


@pytest.fixture
def sdof():
    material = ElasticMaterial(
        material_id="steel",
        youngs_modulus_pa=200e9,
        poisson_ratio=0.3,
        density_kg_m3=7_800,
        yield_strength_pa=250e6,
        source="independent fixture",
    )
    return StructuralModel(
        model_id="sdof",
        stiffness_matrix=((100.0,),),
        mass_matrix=((1.0,),),
        material=material,
        length_m=1.0,
        area_m2=0.01,
        second_moment_m4=1e-6,
    )


def test_v064_static_stress_and_buckling_reference(sdof):
    result = solve_static_structure(model=sdof, load_vector=(100.0,))
    assert result.passed
    assert result.displacements_m["dof_0"] == pytest.approx(1.0)
    assert check_stress(result=result, material=sdof.material).passed


def test_v065_sdof_modes_frequency_response_and_transient(sdof):
    modes = solve_modes(model=sdof, request=ModalRequest(mode_count=1))
    assert modes.passed
    assert modes.frequencies_hz[0] == pytest.approx(1 / (2 * math.pi) * 10)
    frf = solve_frequency_response(
        model=sdof,
        frequencies_hz=(0.0, modes.frequencies_hz[0]),
        force_vector=(1.0,),
        damping=DampingSpec(modal_ratios=(0.05,)),
    )
    assert frf.passed
    assert max(abs(v) for v in frf.response[1]) > abs(frf.response[0][0])
    times = np.linspace(0.0, 1.0, 21)
    transient = solve_transient_response(
        model=sdof,
        times_s=times,
        force_history=np.ones((len(times), 1)),
    )
    assert transient.passed
    assert transient.displacement_m[-1][0] > 0


def test_v065_psd_rms_and_resonance_checks():
    t = np.arange(0.0, 10.0, 0.01)
    x = np.sin(2 * math.pi * 5.0 * t)
    psd = estimate_psd(times_s=t, values=x, unit="m2/Hz")
    assert psd.passed
    assert compute_rms(frequency_hz=psd.frequency_hz, psd=psd.psd) == pytest.approx(1 / math.sqrt(2), rel=0.05)
    assert not check_resonance_margin(
        natural_frequencies_hz=(5.0,), excitation_frequencies_hz=(5.1,), minimum_margin_hz=0.5
    ).passed


def test_v066_fatigue_damage_and_envelope():
    material = FatigueMaterial(
        material_id="test-fatigue",
        sn_points=((100e6, 1e5), (70e6, 1e6)),
        ultimate_strength_pa=500e6,
        source="artificial oracle",
    )
    history = StressHistory(
        history_id="cycle",
        times_s=(0.0, 1.0, 2.0, 3.0, 4.0),
        stress_pa=(0.0, 200e6, 0.0, -200e6, 0.0),
    )
    report = evaluate_fatigue(history=history, material=material, correction=MeanStressCorrection(method="none"))
    assert report.passed
    assert report.damage > 0
    assert check_fatigue_limits(result=report, allowable_damage=1.0).passed
    envelope = evaluate_operating_envelope(
        cases={"nominal": (history, material)},
        scenario_matrix=ScenarioMatrix(cases={"nominal": {"load": 1.0}}),
    )
    assert envelope.passed
    assert envelope.worst_case_id == "nominal"


def test_v066_drive_duty_keeps_signed_energy():
    summary = summarize_drive_duty(
        times_s=(0.0, 1.0, 2.0), torque_nm=(2.0, -2.0, 0.0), speed_rad_s=(3.0, 3.0, 0.0)
    )
    assert summary.passed
    assert summary.energy_positive_j == pytest.approx(6.0)
    assert summary.energy_negative_j == pytest.approx(-6.0)
    assert summary.energy_net_j == pytest.approx(0.0)
