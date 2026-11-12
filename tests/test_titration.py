import pytest

from localchat.titration import (
    INDICATORS,
    TITRATION_FLAVORS,
    equivalence_volume_ml,
    indicator_color,
    titration_ph,
)


def test_equivalence_volume_depends_on_concentrations():
    assert equivalence_volume_ml(0.1, 25, 0.1) == pytest.approx(25)
    assert equivalence_volume_ml(0.1, 25, 0.2) == pytest.approx(12.5)


def test_strong_acid_strong_base_has_neutral_equivalence_and_buffer_sides():
    flavor = TITRATION_FLAVORS[0]
    before = titration_ph(flavor, 0.1, 25, 0.1, 24)
    equivalence = titration_ph(flavor, 0.1, 25, 0.1, 25)
    after = titration_ph(flavor, 0.1, 25, 0.1, 26)

    assert before < 4
    assert equivalence == pytest.approx(7)
    assert after > 10


def test_weak_acid_strong_base_has_buffer_region_and_basic_equivalence():
    flavor = TITRATION_FLAVORS[1]
    initial = titration_ph(flavor, 0.1, 25, 0.1, 0)
    half_equivalence = titration_ph(flavor, 0.1, 25, 0.1, 12.5)
    equivalence = titration_ph(flavor, 0.1, 25, 0.1, 25)

    assert 2 < initial < 4
    assert half_equivalence == pytest.approx(flavor.acid_pka, abs=0.1)
    assert equivalence > 7


def test_strong_acid_weak_base_has_acidic_equivalence():
    flavor = TITRATION_FLAVORS[2]
    equivalence = titration_ph(flavor, 0.1, 25, 0.1, 25)

    assert 4 < equivalence < 7


def test_indicators_have_distinct_colors_in_their_transition_regions():
    assert len(INDICATORS) == 3
    colors = {indicator_color(indicator, 7.0) for indicator in INDICATORS}
    assert len(colors) == 3
