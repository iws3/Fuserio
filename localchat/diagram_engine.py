"""Real-time scientific diagram engine powered by Python Graphviz.

Generates beautiful, space-navy themed architectural flowcharts,
reaction mechanisms, physical circuit paths, and biological process
cycles for Cameroon GCE Ordinary and Advanced Level syllabi.
"""

from __future__ import annotations

import base64
import re
from typing import Optional

try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False


# Fuserio Space-Navy theme attributes for Graphviz DOT
THEME_GRAPH_ATTRS = 'bgcolor="#030d1c" fontname="Helvetica" pad="0.3" rankdir=LR splines=true nodesep=0.45 ranksep=0.6'
THEME_NODE_ATTRS = 'shape=box style="filled,rounded" fillcolor="#082242" color="#58d8d0" fontcolor="#eaf7f5" fontname="Helvetica" fontsize="11" penwidth=1.3 margin="0.18,0.12"'
THEME_EDGE_ATTRS = 'color="#57fabc" fontcolor="#89d4c4" fontname="Helvetica" fontsize="10" arrowhead=vee arrowsize=0.85 penwidth=1.3'


PRESET_DIAGRAMS: dict[str, str] = {
    "titration": """
digraph TitrationWorkflow {
    graph [__GRAPH_ATTRS__ label="\\nACID-BASE VOLUMETRIC ANALYSIS (CAMEROON GCE)" fontcolor="#58d8d0" fontsize=12];
    node [__NODE_ATTRS__];
    edge [__EDGE_ATTRS__];

    Burette [label="Burette\\nStandard Solution (NaOH)\\nKnown Molarity (C_B)", fillcolor="#0a2a4e", color="#389fff"];
    Conical [label="Conical Flask\\nAnalyte (HCl) + Indicator\\nUnknown Conc (C_A)", fillcolor="#0a2a4e", color="#389fff"];
    Equiv [label="Equivalence Point\\nStoichiometric Neutralisation\\nC_A·V_A / C_B·V_B = n_A / n_B", fillcolor="#1a3a28", color="#57fabc"];
    Indicator [label="Phenolphthalein Shift\\nColourless (Acidic)\\n→ Pink / Pale Magenta (Endpoint)", fillcolor="#2a1a38", color="#ff7675"];
    Calculate [label="Titre Calculation\\nAccurate to ±0.05 cm³\\nMean Concordant Titres", fillcolor="#061c34", color="#58d8d0"];

    Burette -> Equiv [label="Dropwise Addition"];
    Conical -> Equiv [label="Analyte"];
    Equiv -> Indicator [label="Visual Endpoint"];
    Indicator -> Calculate [label="Compute Concentration"];
}
""",

    "electrolysis": """
digraph ElectrolysisCell {
    graph [__GRAPH_ATTRS__ label="\\nELECTROLYTIC CELL & IONIC MIGRATION (GCE CHEMISTRY)" fontcolor="#58d8d0" fontsize=12];
    node [__NODE_ATTRS__];
    edge [__EDGE_ATTRS__];

    DC_Power [label="DC Power Source\\nBattery / Rectifier", fillcolor="#0a264a", color="#389fff"];
    Anode [label="Anode (+)\\nOxidation Occurs\\n2Cl⁻ → Cl₂(g) + 2e⁻", fillcolor="#2a1622", color="#ff7675"];
    Cathode [label="Cathode (-)\\nReduction Occurs\\nCu²⁺ + 2e⁻ → Cu(s)", fillcolor="#122a20", color="#57fabc"];
    Electrolyte [label="Electrolyte (Aqueous)\\nCuCl₂(aq) Solution\\nCu²⁺ & Cl⁻ Ions", fillcolor="#082242", color="#58d8d0"];

    DC_Power -> Anode [label="Current (+)"];
    DC_Power -> Cathode [label="Electrons (-)"];
    Electrolyte -> Anode [label="Anions Migrate (Cl⁻)"];
    Electrolyte -> Cathode [label="Cations Migrate (Cu²⁺)"];
}
""",

    "reaction_rate": """
digraph ReactionKinetics {
    graph [__GRAPH_ATTRS__ label="\\nCOLLISION THEORY & ACTIVATION ENERGY (KINETICS)" fontcolor="#58d8d0" fontsize=12];
    node [__NODE_ATTRS__];
    edge [__EDGE_ATTRS__];

    Reactants [label="Reactant Molecules\\nSufficient Kinetic Energy\\nCorrect Molecular Orientation", fillcolor="#0a2444", color="#389fff"];
    Barrier [label="Activation Energy (E_a)\\nMinimum Energy Required\\nfor Effective Collision", fillcolor="#2a2010", color="#ffb84d"];
    Catalyst [label="Catalyst Action\\nAlternative Reaction Path\\nLowers Activation Energy", fillcolor="#123024", color="#57fabc"];
    Complex [label="Activated Complex\\nTransition State", fillcolor="#241434", color="#a55eea"];
    Products [label="Reaction Products\\nΔH Reaction Enthalpy\\nExothermic / Endothermic", fillcolor="#061e38", color="#58d8d0"];

    Reactants -> Barrier [label="Collisions"];
    Catalyst -> Barrier [label="Lowers E_a"];
    Barrier -> Complex [label="E ≥ E_a"];
    Complex -> Products [label="Form Bonds"];
}
""",

    "salts_prep": """
digraph SaltsPreparation {
    graph [__GRAPH_ATTRS__ label="\\nPREPARATION OF INSOLUBLE SALTS (PRECIPITATION)" fontcolor="#58d8d0" fontsize=12];
    node [__NODE_ATTRS__];
    edge [__EDGE_ATTRS__];

    SolutionA [label="Soluble Salt A\\ne.g. Pb(NO₃)₂(aq)", fillcolor="#082444", color="#389fff"];
    SolutionB [label="Soluble Salt B\\ne.g. 2KI(aq)", fillcolor="#082444", color="#389fff"];
    Mix [label="Mixing & Reaction\\nPrecipitate Forms Immediately", fillcolor="#182c44", color="#58d8d0"];
    Filter [label="Gravity Filtration\\nFunnel & Filter Paper\\nResidue vs Filtrate", fillcolor="#1a3224", color="#57fabc"];
    Residue [label="Residue: Insoluble Salt\\ne.g. Bright Yellow PbI₂(s)", fillcolor="#2c2810", color="#ffb84d"];
    Dry [label="Wash & Dry\\nRinse with distilled H₂O\\nDry between filter papers", fillcolor="#0a2846", color="#57fabc"];

    SolutionA -> Mix [label="Combine"];
    SolutionB -> Mix;
    Mix -> Filter [label="Pour onto filter"];
    Filter -> Residue [label="Collected"];
    Residue -> Dry [label="Pure Dry Salt"];
}
""",

    "pendulum": """
digraph SimplePendulum {
    graph [__GRAPH_ATTRS__ label="\\nSIMPLE HARMONIC MOTION & ENERGY CONSERVATION" fontcolor="#58d8d0" fontsize=12];
    node [__NODE_ATTRS__];
    edge [__EDGE_ATTRS__];

    Extreme [label="Extreme Position (+θ)\\nVelocity v = 0\\nMax Potential Energy E_p = mgh\\nRestoring Force F = -mg sin(θ)", fillcolor="#241e0e", color="#ffb84d"];
    Equilibrium [label="Mean Equilibrium (θ = 0)\\nMax Velocity v_max\\nMax Kinetic Energy E_k = ½mv²\\nRestoring Force = 0", fillcolor="#102e24", color="#57fabc"];
    Formula [label="GCE Formula\\nPeriod T = 2π√(L/g)\\ng = 4π²L / T²", fillcolor="#061c34", color="#389fff"];

    Extreme -> Equilibrium [label="E_p → E_k (Accelerating)"];
    Equilibrium -> Extreme [label="E_k → E_p (Decelerating)"];
    Equilibrium -> Formula [label="Determine g"];
}
""",

    "refraction": """
digraph SnellLaw {
    graph [__GRAPH_ATTRS__ label="\\nSNELL'S LAW & LIGHT REFRACTION AT INTERFACE" fontcolor="#58d8d0" fontsize=12];
    node [__NODE_ATTRS__];
    edge [__EDGE_ATTRS__];

    Incident [label="Incident Ray\\nAngle of Incidence (i)\\nMedium 1: Air (n₁ ≈ 1.0)", fillcolor="#0a264a", color="#389fff"];
    Interface [label="Optical Boundary\\nNormal Line (Perpendicular)\\nChange in Wave Velocity v₁ → v₂", fillcolor="#182a44", color="#58d8d0"];
    Refracted [label="Refracted Ray\\nAngle of Refraction (r)\\nMedium 2: Glass (n₂ > n₁)\\nBends TOWARDS normal", fillcolor="#122a22", color="#57fabc"];
    Snell [label="Snell's Law Formula\\n(sin i) / (sin r) = n₂/n₁\\nn = v₁ / v₂ = λ₁ / λ₂", fillcolor="#061a32", color="#ffb84d"];

    Incident -> Interface [label="Enters boundary"];
    Interface -> Refracted [label="Slows down in dense medium"];
    Refracted -> Snell [label="Constant Ratio"];
}
""",

    "circuits": """
digraph OhmCircuits {
    graph [__GRAPH_ATTRS__ label="\\nCIRCUIT ANALYSIS & OHM'S LAW (PHYSICS)" fontcolor="#58d8d0" fontsize=12];
    node [__NODE_ATTRS__];
    edge [__EDGE_ATTRS__];

    EMF [label="EMF Source (Battery)\\nTotal Voltage V\\nInternal Resistance r", fillcolor="#0a2648", color="#389fff"];
    Series [label="Series Circuit\\nI_total = I₁ = I₂\\nR_total = R₁ + R₂\\nV_total = V₁ + V₂", fillcolor="#162c3e", color="#58d8d0"];
    Parallel [label="Parallel Circuit\\nV_total = V₁ = V₂\\n1/R_total = 1/R₁ + 1/R₂\\nI_total = I₁ + I₂", fillcolor="#142c22", color="#57fabc"];
    Ohm [label="Ohm's Law\\nV = I · R\\nP = V · I = I²R", fillcolor="#282210", color="#ffb84d"];

    EMF -> Series [label="Single Current Path"];
    EMF -> Parallel [label="Multiple Current Paths"];
    Series -> Ohm;
    Parallel -> Ohm;
}
""",

    "photosynthesis": """
digraph PhotosynthesisCycle {
    graph [__GRAPH_ATTRS__ label="\\nPHOTOSYNTHESIS BIOCHEMICAL PATHWAYS (GCE BIOLOGY)" fontcolor="#58d8d0" fontsize=12];
    node [__NODE_ATTRS__];
    edge [__EDGE_ATTRS__];

    Light [label="Light Reactions\\nThylakoid Membrane\\nChlorophyll absorbs light\\nH₂O Photolysis → O₂ + 2H⁺ + 2e⁻", fillcolor="#0e2a3c", color="#389fff"];
    Energy [label="Energy Carriers\\nATP + NADPH Generated", fillcolor="#28220c", color="#ffb84d"];
    Calvin [label="Calvin Cycle (Dark Phase)\\nStroma of Chloroplast\\nRuBisCO CO₂ Fixation\\nRuBP + CO₂ → GP → TP", fillcolor="#102e20", color="#57fabc"];
    Glucose [label="Final Biomass\\nGlucose (C₆H₁₂O₆)\\nConverted to Starch / Cellulose", fillcolor="#082038", color="#58d8d0"];

    Light -> Energy [label="Photophosphorylation"];
    Energy -> Calvin [label="Reduces Carbon"];
    Calvin -> Glucose [label="Hexose Synthesis"];
}
""",

    "respiration": """
digraph CellularRespiration {
    graph [__GRAPH_ATTRS__ label="\\nAEROBIC CELLULAR RESPIRATION (MITOCHONDRIA)" fontcolor="#58d8d0" fontsize=12];
    node [__NODE_ATTRS__];
    edge [__EDGE_ATTRS__];

    Glycolysis [label="1. Glycolysis\\nCytoplasm (Anaerobic)\\nGlucose (6C) → 2 Pyruvate (3C)\\nNet Gain: 2 ATP + 2 NADH", fillcolor="#0a264a", color="#389fff"];
    Link [label="2. Link Reaction\\nMitochondrial Matrix\\nPyruvate → Acetyl-CoA (2C) + CO₂", fillcolor="#142844", color="#58d8d0"];
    Krebs [label="3. Krebs (TCA) Cycle\\nMitochondrial Matrix\\nOxaloacetate (4C) + Acetyl-CoA → Citrate\\nProduces: 2 ATP + 6 NADH + 2 FADH₂ + 4 CO₂", fillcolor="#102e22", color="#57fabc"];
    ETC [label="4. Electron Transport Chain\\nInner Mitochondrial Cristae\\nOxidative Phosphorylation\\nATP Synthase Proton Gradient\\nYield: ~32-34 ATP + H₂O", fillcolor="#261c0e", color="#ffb84d"];

    Glycolysis -> Link [label="Pyruvate transport"];
    Link -> Krebs [label="Acetyl-CoA enters"];
    Krebs -> ETC [label="NADH & FADH₂ donate e⁻"];
}
""",

    "mitosis": """
digraph MitosisPhases {
    graph [__GRAPH_ATTRS__ label="\\nMITOSIS: SOMATIC CELL DIVISION (2n → 2n)" fontcolor="#58d8d0" fontsize=12];
    node [__NODE_ATTRS__];
    edge [__EDGE_ATTRS__];

    Interphase [label="Interphase (G₁, S, G₂)\\nDNA Replication\\nCentrosome Duplication", fillcolor="#0a2444", color="#389fff"];
    Prophase [label="Prophase\\nChromosomes condense\\nNuclear envelope breaks down\\nSpindle fibres form", fillcolor="#142646", color="#58d8d0"];
    Metaphase [label="Metaphase\\nChromosomes align at equator\\n(Metaphase plate)\\nSpindle attaches to centromere", fillcolor="#102e22", color="#57fabc"];
    Anaphase [label="Anaphase\\nSister chromatids pulled apart\\nto opposite cell poles", fillcolor="#262010", color="#ffb84d"];
    Telophase [label="Telophase & Cytokinesis\\nTwo genetically identical\\ndiploid daughter cells (2n)", fillcolor="#26142a", color="#a55eea"];

    Interphase -> Prophase;
    Prophase -> Metaphase;
    Metaphase -> Anaphase;
    Anaphase -> Telophase;
}
""",

    "enzyme": """
digraph EnzymeKinetics {
    graph [__GRAPH_ATTRS__ label="\\nENZYME-SUBSTRATE KINETICS (LOCK & KEY HYPOTHESIS)" fontcolor="#58d8d0" fontsize=12];
    node [__NODE_ATTRS__];
    edge [__EDGE_ATTRS__];

    Enzyme [label="Free Enzyme\\nActive site with complementary shape", fillcolor="#0a2444", color="#389fff"];
    Substrate [label="Substrate Molecule\\nSpecific chemical reactant", fillcolor="#082242", color="#58d8d0"];
    Complex [label="Enzyme-Substrate Complex (ES)\\nTemporary intermediate bonds\\nStrains substrate bonds", fillcolor="#142e22", color="#57fabc"];
    Products [label="Reaction Products\\nProducts released from active site\\nEnzyme remains unchanged", fillcolor="#261e0e", color="#ffb84d"];

    Enzyme -> Complex [label="Binds at active site"];
    Substrate -> Complex;
    Complex -> Products [label="Catalysis"];
    Products -> Enzyme [label="Enzyme reused", style=dashed];
}
""",

    "quadratic": """
digraph QuadraticFormula {
    graph [__GRAPH_ATTRS__ label="\\nQUADRATIC EQUATION ANALYSIS: ax² + bx + c = 0" fontcolor="#58d8d0" fontsize=12];
    node [__NODE_ATTRS__];
    edge [__EDGE_ATTRS__];

    Eq [label="Standard Form\\nax² + bx + c = 0", fillcolor="#0a264a", color="#389fff"];
    Disc [label="Compute Discriminant\\nΔ = b² - 4ac", fillcolor="#182c44", color="#58d8d0"];
    Case1 [label="Δ > 0\\nTwo Distinct Real Roots\\nx = (-b ± √Δ) / 2a", fillcolor="#102e20", color="#57fabc"];
    Case2 [label="Δ = 0\\nOne Repeated (Equal) Real Root\\nx = -b / 2a", fillcolor="#282210", color="#ffb84d"];
    Case3 [label="Δ < 0\\nTwo Complex Conjugate Roots\\nNo real x-intercepts", fillcolor="#24142a", color="#a55eea"];

    Eq -> Disc;
    Disc -> Case1 [label="Positive"];
    Disc -> Case2 [label="Zero"];
    Disc -> Case3 [label="Negative"];
}
""",

    "trigonometry": """
digraph TrigonometryFramework {
    graph [__GRAPH_ATTRS__ label="\\nTRIGONOMETRY & CIRCULAR FUNCTIONS (CAMEROON GCE)" fontcolor="#58d8d0" fontsize=12];
    node [__NODE_ATTRS__];
    edge [__EDGE_ATTRS__];

    RightTriangle [label="Right-Angled Triangle\\nHypotenuse, Opposite, Adjacent\\nPythagoras: a² + b² = c²", fillcolor="#0a264a", color="#389fff"];
    Ratios [label="Basic Ratios (SOH CAH TOA)\\nsin(θ) = Opp / Hyp\\ncos(θ) = Adj / Hyp\\ntan(θ) = Opp / Adj", fillcolor="#182c44", color="#58d8d0"];
    UnitCircle [label="Unit Circle (r = 1)\\nx = cos(θ), y = sin(θ)\\nRadians: π rad = 180°", fillcolor="#102e22", color="#57fabc"];
    Identities [label="Pythagorean Identities\\nsin²(θ) + cos²(θ) = 1\\n1 + tan²(θ) = sec²(θ)", fillcolor="#282010", color="#ffb84d"];
    TriangleLaws [label="Non-Right Triangles\\nSine Rule: a/sin(A) = b/sin(B)\\nCosine Rule: c² = a² + b² - 2ab cos(C)", fillcolor="#24142a", color="#a55eea"];

    RightTriangle -> Ratios [label="ratios"];
    Ratios -> UnitCircle [label="all angles"];
    UnitCircle -> Identities [label="derive"];
    Ratios -> TriangleLaws [label="generalise"];
}
""",

    "calculus": """
digraph CalculusFramework {
    graph [__GRAPH_ATTRS__ label="\\nCALCULUS & ANALYSIS (GCE ADVANCED LEVEL)" fontcolor="#58d8d0" fontsize=12];
    node [__NODE_ATTRS__];
    edge [__EDGE_ATTRS__];

    Function [label="Function y = f(x)\\nDomain & Continuity", fillcolor="#0a264a", color="#389fff"];
    Diff [label="Differentiation (dy/dx)\\nInstantaneous Rate of Change\\nGradient of Tangent Curve", fillcolor="#182c44", color="#58d8d0"];
    Extrema [label="Stationary Points\\ndy/dx = 0 (Maxima / Minima)\\nd²y/dx² Curvature Test", fillcolor="#282010", color="#ffb84d"];
    Integral [label="Integration (∫ f(x) dx)\\nAnti-derivative + Constant C\\nArea Under the Curve", fillcolor="#102e22", color="#57fabc"];
    FTC [label="Fundamental Theorem\\n∫ₐᵇ f(x) dx = F(b) - F(a)\\nDefinite Net Accumulation", fillcolor="#24142a", color="#a55eea"];

    Function -> Diff [label="d/dx"];
    Diff -> Extrema [label="optimise"];
    Function -> Integral [label="integrate"];
    Integral -> FTC [label="evaluate limits"];
    Diff -> Integral [label="inverse operations", dir=both];
}
""",

    "newton": """
digraph NewtonMechanics {
    graph [__GRAPH_ATTRS__ label="\\nNEWTONIAN MECHANICS & DYNAMICS (GCE PHYSICS)" fontcolor="#58d8d0" fontsize=12];
    node [__NODE_ATTRS__];
    edge [__EDGE_ATTRS__];

    FirstLaw [label="Newton's 1st Law (Inertia)\\nΣF = 0 ⟹ Δv = 0\\nUniform velocity or rest", fillcolor="#0a264a", color="#389fff"];
    SecondLaw [label="Newton's 2nd Law (Force)\\nF_net = dp/dt = m · a\\nResultant force accelerates body", fillcolor="#182c44", color="#58d8d0"];
    ThirdLaw [label="Newton's 3rd Law (Action/Reaction)\\nF_AB = - F_BA\\nEqual magnitude, opposite sense", fillcolor="#102e22", color="#57fabc"];
    Momentum [label="Conservation of Momentum\\nΣp_initial = Σp_final\\nm₁u₁ + m₂u₂ = m₁v₁ + m₂v₂", fillcolor="#282010", color="#ffb84d"];

    FirstLaw -> SecondLaw [label="applied net force"];
    SecondLaw -> ThirdLaw [label="two-body interaction"];
    SecondLaw -> Momentum [label="impulse F·Δt = Δp"];
}
"""
}


def _prepare_dot(dot_source: str) -> str:
    """Injects standard dark space-navy theme into DOT source if placeholders are present."""
    return (
        dot_source
        .replace("__GRAPH_ATTRS__", THEME_GRAPH_ATTRS)
        .replace("__NODE_ATTRS__", THEME_NODE_ATTRS)
        .replace("__EDGE_ATTRS__", THEME_EDGE_ATTRS)
    )


def render_dot_to_base64_png(dot_source: str) -> Optional[str]:
    """Compiles a DOT string using Graphviz in Python and returns base64 PNG data."""
    if not HAS_GRAPHVIZ:
        return None
    try:
        clean_dot = _prepare_dot(dot_source)
        # Ensure bgcolor is dark space-navy if not explicitly defined
        if "bgcolor" not in clean_dot:
            clean_dot = clean_dot.replace("graph [", f"graph [{THEME_GRAPH_ATTRS} ", 1)

        src = graphviz.Source(clean_dot)
        png_data = src.pipe(format="png")
        if not png_data:
            return None
        return base64.b64encode(png_data).decode("ascii")
    except Exception:
        return None


def get_topic_diagram(query: str) -> Optional[str]:
    """Matches a user query or topic to a curated Cameroon GCE scientific diagram."""
    q = query.lower().strip()
    # Clean conversational filler phrases
    q = re.sub(
        r"^(?:figure\s*(?:of|for|:)?\s*|diagram\s*(?:of|for|:)?\s*|explain\s*(?:about|on|the)?\s*|about\s*|a\s+|the\s+)+",
        "",
        q,
        flags=re.IGNORECASE,
    ).strip()

    if any(k in q for k in ["titrat", "acid", "base", "neutral", "phenolphthalein", "burette"]):
        return PRESET_DIAGRAMS.get("titration")
    if any(k in q for k in ["electrolysis", "anode", "cathode", "electrolyte", "ionic migration"]):
        return PRESET_DIAGRAMS.get("electrolysis")
    if any(k in q for k in ["reaction rate", "collision theory", "activation energy", "catalyst", "kinetics"]):
        return PRESET_DIAGRAMS.get("reaction_rate")
    if any(k in q for k in ["precipitat", "salt", "insoluble", "filtration", "preparation of salts"]):
        return PRESET_DIAGRAMS.get("salts_prep")
    if any(k in q for k in ["pendulum", "simple harmonic", "gravitational period", "shm"]):
        return PRESET_DIAGRAMS.get("pendulum")
    if any(k in q for k in ["refract", "snell", "optical density", "lens", "incident"]):
        return PRESET_DIAGRAMS.get("refraction")
    if any(k in q for k in ["circuit", "ohm", "voltage", "current", "resistor", "kirchhoff"]):
        return PRESET_DIAGRAMS.get("circuits")
    if any(k in q for k in ["newton", "force", "acceleration", "f=ma", "mechanics", "momentum"]):
        return PRESET_DIAGRAMS.get("newton")
    if any(k in q for k in ["photosynthesis", "calvin", "thylakoid", "chlorophyll", "chloroplast"]):
        return PRESET_DIAGRAMS.get("photosynthesis")
    if any(k in q for k in ["respiration", "krebs", "glycolysis", "mitochondria", "atp synthase"]):
        return PRESET_DIAGRAMS.get("respiration")
    if any(k in q for k in ["mitosis", "metaphase", "anaphase", "prophase", "cell division"]):
        return PRESET_DIAGRAMS.get("mitosis")
    if any(k in q for k in ["enzyme", "substrate", "lock and key", "active site", "denatur"]):
        return PRESET_DIAGRAMS.get("enzyme")
    if any(k in q for k in ["trigonometr", "trig", "sohcahtoa", "sine", "cosine", "tangent", "unit circle", "pythagor"]):
        return PRESET_DIAGRAMS.get("trigonometry")
    if any(k in q for k in ["calculus", "differentiat", "integrat", "derivative", "anti-derivative"]):
        return PRESET_DIAGRAMS.get("calculus")
    if any(k in q for k in ["quadratic", "discriminant", "roots of"]):
        return PRESET_DIAGRAMS.get("quadratic")

    return None


def render_markdown_diagrams(text: str) -> str:
    """Parses markdown for ```dot or ```graphviz blocks, rendering them to real-time PNG base64 images."""
    if not text:
        return ""

    # Match ```dot ... ``` or ```graphviz ... ```
    pattern = re.compile(r"```(?:dot|graphviz)\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)

    def _replace_block(match: re.Match) -> str:
        dot_code = match.group(1).strip()
        b64_png = render_dot_to_base64_png(dot_code)
        if not b64_png:
            return match.group(0)

        return (
            '<div style="margin: 12px 0; background: rgba(3, 14, 28, 0.95); border: 1px solid rgba(88, 216, 208, 0.4); border-radius: 8px; padding: 12px; text-align: center;">'
            f'<div style="color: #57fabc; font-family: monospace; font-size: 10px; font-weight: bold; margin-bottom: 8px; text-align: left;">'
            f'📊 REAL-TIME GRAPHVIZ DIAGRAM · GCE CURRICULUM</div>'
            f'<img src="data:image/png;base64,{b64_png}" style="max-width: 100%; border-radius: 4px;" />'
            '</div>'
        )

    return pattern.sub(_replace_block, text)


def render_diagram_card(dot_source: str, title: str = "SCIENTIFIC PROCESS DIAGRAM") -> str:
    """Renders a standalone DOT diagram card with styled frame."""
    b64_png = render_dot_to_base64_png(dot_source)
    if not b64_png:
        return ""

    return (
        '<div style="margin: 14px 0 10px 0; background: rgba(3, 14, 28, 0.95); border: 1px solid rgba(88, 216, 208, 0.45); border-left: 3px solid #57fabc; border-radius: 8px; padding: 12px; text-align: center;">'
        f'<div style="color: #57fabc; font-family: monospace; font-size: 10px; font-weight: bold; margin-bottom: 8px; text-align: left;">'
        f'📊 GRAPHVIZ ARCHITECTURE · {title}</div>'
        f'<img src="data:image/png;base64,{b64_png}" style="max-width: 100%; border-radius: 4px;" />'
        '</div>'
    )
