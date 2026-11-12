from dataclasses import dataclass
import math


@dataclass(frozen=True)
class TitrationFlavor:
    identifier: str
    label: str
    analyte: str
    titrant: str
    acid_kind: str
    base_kind: str
    acid_pka: float | None = None
    conjugate_acid_pka: float | None = None


TITRATION_FLAVORS = (
    TitrationFlavor(
        "strong-strong",
        "Strong acid + strong base",
        "Hydrochloric acid (HCl)",
        "Sodium hydroxide (NaOH)",
        "strong",
        "strong",
    ),
    TitrationFlavor(
        "weak-strong",
        "Weak acid + strong base",
        "Ethanoic acid (CH₃COOH)",
        "Sodium hydroxide (NaOH)",
        "weak",
        "strong",
        acid_pka=4.76,
    ),
    TitrationFlavor(
        "strong-weak",
        "Strong acid + weak base",
        "Hydrochloric acid (HCl)",
        "Ammonia solution (NH₃)",
        "strong",
        "weak",
        conjugate_acid_pka=9.25,
    ),
)

INDICATORS = (
    "Phenolphthalein",
    "Methyl orange",
    "Bromothymol blue",
)


def flavor_by_id(identifier: str) -> TitrationFlavor:
    return next((flavor for flavor in TITRATION_FLAVORS if flavor.identifier == identifier), TITRATION_FLAVORS[0])


def equivalence_volume_ml(
    acid_molarity: float,
    acid_volume_ml: float,
    base_molarity: float,
) -> float:
    if acid_molarity <= 0 or acid_volume_ml <= 0 or base_molarity <= 0:
        raise ValueError("Concentrations and analyte volume must be positive.")
    return acid_molarity * acid_volume_ml / base_molarity


def titration_ph(
    flavor: TitrationFlavor,
    acid_molarity: float,
    acid_volume_ml: float,
    base_molarity: float,
    base_volume_ml: float,
) -> float:
    """Approximate pH for a monoprotic titration using mole balance and buffer regions."""
    if min(acid_molarity, acid_volume_ml, base_molarity) <= 0 or base_volume_ml < 0:
        raise ValueError("Use positive concentrations/volume and a non-negative titrant volume.")

    acid_moles = acid_molarity * acid_volume_ml / 1000
    base_moles = base_molarity * base_volume_ml / 1000
    total_litres = (acid_volume_ml + base_volume_ml) / 1000
    difference = acid_moles - base_moles
    equivalence = acid_moles
    epsilon = max(acid_moles, base_moles, 1.0) * 1e-12

    if flavor.base_kind == "weak":
        pka = flavor.conjugate_acid_pka or 9.25
        if difference > epsilon:
            hydrogen_concentration = difference / total_litres
            return max(0.0, min(14.0, -math.log10(max(hydrogen_concentration, 1e-14))))
        if abs(difference) <= epsilon:
            salt_concentration = acid_moles / total_litres
            return max(0.0, min(14.0, 0.5 * (pka - math.log10(max(salt_concentration, 1e-14)))))
        ammonia_moles = -difference
        ammonium_moles = equivalence
        ratio = ammonia_moles / ammonium_moles
        return max(0.0, min(14.0, pka + math.log10(max(ratio, 1e-14))))

    if flavor.acid_kind == "strong":
        if difference > epsilon:
            hydrogen_concentration = difference / total_litres
            return max(0.0, min(14.0, -math.log10(max(hydrogen_concentration, 1e-14))))
        if abs(difference) <= epsilon:
            return 7.0
        hydroxide_concentration = -difference / total_litres
        return max(0.0, min(14.0, 14 + math.log10(max(hydroxide_concentration, 1e-14))))

    pka = flavor.acid_pka or 4.76
    if base_moles <= epsilon:
        ka = 10 ** -pka
        concentration = acid_molarity
        hydrogen = (-ka + math.sqrt(ka * ka + 4 * ka * concentration)) / 2
        return max(0.0, min(14.0, -math.log10(max(hydrogen, 1e-14))))
    if difference > epsilon:
        return max(0.0, min(14.0, pka + math.log10(base_moles / difference)))
    if abs(difference) <= epsilon:
        salt_concentration = acid_moles / total_litres
        kb = 1e-14 / (10 ** -pka)
        hydroxide = math.sqrt(kb * salt_concentration)
        return max(0.0, min(14.0, 14 + math.log10(max(hydroxide, 1e-14))))
    hydroxide_concentration = -difference / total_litres
    return max(0.0, min(14.0, 14 + math.log10(max(hydroxide_concentration, 1e-14))))


def indicator_color(indicator: str, ph: float) -> tuple[int, int, int]:
    if indicator == "Methyl orange":
        if ph < 3.1:
            return (235, 82, 77)
        if ph < 4.4:
            blend = (ph - 3.1) / 1.3
            return (235, int(82 + 113 * blend), int(77 - 7 * blend))
        return (235, 188, 65)
    if indicator == "Bromothymol blue":
        if ph < 6.0:
            return (238, 199, 61)
        if ph < 7.6:
            blend = (ph - 6.0) / 1.6
            return (int(238 - 180 * blend), int(199 - 17 * blend), int(61 + 145 * blend))
        return (58, 182, 220)
    if ph < 8.2:
        return (193, 205, 198)
    if ph < 10.0:
        blend = (ph - 8.2) / 1.8
        return (int(193 + 62 * blend), int(205 - 105 * blend), int(198 + 10 * blend))
    return (255, 104, 173)
