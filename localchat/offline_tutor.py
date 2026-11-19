"""Offline intelligence and Cameroon GCE knowledge base for Fuserio.

Provides instant, rich, step-by-step responses for Cameroon secondary
and high school students (Ordinary Level and Advanced Level) even when
operating 100% offline without a local llama.cpp server running.
"""

import re
from typing import Tuple


def generate_offline_gce_response(
    query: str, subject: str = "", level: str = ""
) -> Tuple[str, str]:
    """Generates (think_trace_reasoning, formatted_markdown_response)."""
    q = query.lower()
    subj = subject or _detect_subject(q)
    lvl = level or "Ordinary Level"

    reasoning = (
        f"1. Context identification: Subject = {subj or 'General Science'}, Level = {lvl}.\n"
        f"2. Student Query: '{query.strip()}'.\n"
        f"3. Retrieved Cameroon GCE syllabus scaffolds and exam marking points.\n"
        f"4. Structuring response: Core concept definition, key equations/laws, "
        f"and a step-by-step worked examination example."
    )

    # 1. Physics Topics
    if any(k in q for k in ["newton", "force", "acceleration", "f=ma", "momentum"]):
        content = (
            "### Newton's Laws of Motion (Cameroon GCE Physics)\n\n"
            "**Core Law Statement (Newton's 2nd Law):**\n"
            "The rate of change of momentum of a body is directly proportional to the "
            "applied resultant force, and occurs in the direction of the force.\n\n"
            "$$\\mathbf{F}_{\\text{net}} = m \\cdot \\mathbf{a}$$\n\n"
            "* $F$ = Net resultant force (measured in **Newtons, N**)\n"
            "* $m$ = Mass of the body (measured in **kg**)\n"
            "* $a$ = Acceleration (measured in **m/s²**)\n\n"
            "#### Cameroon GCE Worked Example:\n"
            "**Question:** A stationary truck of mass $1200\\text{ kg}$ reaches a velocity "
            "of $24\\text{ m/s}$ in $8\\text{ seconds}$. Calculate the resultant forward force.\n\n"
            "1. **Determine acceleration ($a$):**\n"
            "   $$a = \\frac{v - u}{t} = \\frac{24 - 0}{8} = 3\\text{ m/s}^2$$\n"
            "2. **Apply Newton's Second Law ($F = m \\cdot a$):**\n"
            "   $$F = 1200\\text{ kg} \\times 3\\text{ m/s}^2 = \\mathbf{3600\\text{ N}}$$\n\n"
            "> **GCE Exam Tip:** Always write the formula first for 1 method mark, substitute with units, "
            "and state the final answer with correct SI units."
        )
        return reasoning, content

    if any(k in q for k in ["ohm", "resistan", "voltage", "current", "circuit", "v=ir"]):
        content = (
            "### Ohm's Law & Circuit Analysis (Cameroon GCE Physics)\n\n"
            "**Ohm's Law:**\n"
            "The current passing through a metallic conductor is directly proportional "
            "to the potential difference across its ends, provided temperature and other physical conditions remain constant.\n\n"
            "$$V = I \\cdot R$$\n\n"
            "* $V$ = Potential difference / Voltage (**Volts, V**)\n"
            "* $I$ = Current (**Amperes, A**)\n"
            "* $R$ = Electrical resistance (**Ohms, \\Omega**)\n\n"
            "#### Resistor Combinations:\n"
            "* **Series:** $R_{\\text{total}} = R_1 + R_2 + R_3$\n"
            "* **Parallel:** $\\frac{1}{R_{\\text{total}}} = \\frac{1}{R_1} + \\frac{1}{R_2}$\n\n"
            "#### Quick GCE Check Question:\n"
            "If a $12\\text{ V}$ battery is connected across two resistors of $4\\,\\Omega$ and $6\\,\\Omega$ in series:\n"
            "$$R_{\\text{total}} = 4 + 6 = 10\\,\\Omega$$\n"
            "$$I = \\frac{V}{R} = \\frac{12}{10} = \\mathbf{1.2\\text{ A}}$$"
        )
        return reasoning, content

    if any(k in q for k in ["pendulum", "oscillation", "periodic", "simple harmonic"]):
        content = (
            "### Simple Pendulum & Periodic Time\n\n"
            "A simple pendulum executes simple harmonic motion (SHM) for small angular displacements ($\theta < 10^\\circ$).\n\n"
            "$$T = 2\\pi \\sqrt{\\frac{L}{g}}$$\n\n"
            "* $T$ = Period of one complete oscillation (**seconds, s**)\n"
            "* $L$ = Length of the pendulum string to centre of gravity (**metres, m**)\n"
            "* $g$ = Acceleration due to gravity (approx. $9.8\\text{ m/s}^2$)\n\n"
            "**Key Lab Observations:**\n"
            "1. Period $T$ is **independent** of the mass of the bob.\n"
            "2. Period $T$ is **independent** of small amplitude ($\theta < 10^\\circ$).\n"
            "3. $T^2$ plotted against $L$ yields a straight line through the origin with slope $\\frac{4\\pi^2}{g}$."
        )
        return reasoning, content

    if any(k in q for k in ["projectile", "trajectory", "horizontal range"]):
        content = (
            "### Projectile Motion (GCE Advanced Level)\n\n"
            "A projectile moves under gravity with zero horizontal acceleration ($a_x = 0$) "
            "and constant vertical downward acceleration ($a_y = -g$).\n\n"
            "* **Time of flight ($T$):** $T = \\frac{2 u \\sin\\theta}{g}$\n"
            "* **Maximum height ($H$):** $H = \\frac{u^2 \\sin^2\\theta}{2g}$\n"
            "* **Horizontal range ($R$):** $R = \\frac{u^2 \\sin(2\\theta)}{g}$\n\n"
            "> **Key Note:** Maximum horizontal range is achieved when launch angle $\\theta = 45^\\circ$."
        )
        return reasoning, content

    if any(k in q for k in ["refraction", "snell", "light", "lens", "reflection"]):
        content = (
            "### Refraction & Snell's Law (Cameroon GCE Physics)\n\n"
            "Refraction is the bending of light as it passes from one optical medium into another of different optical density.\n\n"
            "**Snell's Law:**\n"
            "$$\\frac{\\sin i}{\\sin r} = n = \\frac{v_1}{v_2}$$\n\n"
            "* $i$ = Angle of incidence\n"
            "* $r$ = Angle of refraction\n"
            "* $n$ = Refractive index of the second medium relative to the first"
        )
        return reasoning, content

    # 2. Chemistry Topics
    if any(k in q for k in ["titrat", "acid", "base", "neutral", "phenolphthalein", "methyl orange"]):
        content = (
            "### Acid-Base Titration (Volumetric Analysis)\n\n"
            "Titration is an analytical technique used to determine the unknown concentration "
            "of an analyte using a standard solution of known concentration.\n\n"
            "$$\\frac{C_A \\cdot V_A}{C_B \\cdot V_B} = \\frac{n_A}{n_B}$$\n\n"
            "* $C_A, C_B$ = Molar concentrations (mol/dm³ or M)\n"
            "* $V_A, V_B$ = Titre volumes (cm³ or mL)\n"
            "* $n_A, n_B$ = Stoichiometric mole ratio from balanced chemical equation\n\n"
            "#### Common Cameroon GCE Indicators:\n"
            "1. **Phenolphthalein:** Colourless in acid, pink at endpoint (pH 8.2 - 10.0).\n"
            "2. **Methyl Orange:** Red in acid, yellow/orange at endpoint (pH 3.1 - 4.4).\n\n"
            "#### Pre-Lab Precautions:\n"
            "* Rinse the burette with the solution it is to contain before filling.\n"
            "* Ensure no air bubbles remain beneath the burette stopcock.\n"
            "* Read the bottom of the meniscus at eye level."
        )
        return reasoning, content

    if any(k in q for k in ["rate of reaction", "catalyst", "activation energy", "collision"]):
        content = (
            "### Rates of Chemical Reactions\n\n"
            "According to **Collision Theory**, for a reaction to occur, reactant particles must collide "
            "with sufficient energy ($E \\ge E_a$, the activation energy) and correct orientation.\n\n"
            "$$\\text{Rate} = \\frac{\\Delta[\\text{Concentration}]}{\\Delta t}$$\n\n"
            "**Factors Affecting Reaction Rate:**\n"
            "1. **Concentration / Pressure:** Increases collision frequency.\n"
            "2. **Temperature:** Increases average kinetic energy; more particles exceed $E_a$.\n"
            "3. **Surface Area:** Exposes more active reactant sites.\n"
            "4. **Catalyst:** Provides an alternative reaction pathway with lower activation energy."
        )
        return reasoning, content

    if any(k in q for k in ["salt", "solubility", "precipitation", "precipitate"]):
        content = (
            "### Salts, Solubility & Precipitation (Cameroon GCE Chemistry)\n\n"
            "A precipitation reaction occurs when two soluble salts react in aqueous solution to form an insoluble solid.\n\n"
            "**General Solubility Rules:**\n"
            "* **All nitrates ($NO_3^-$)** and **Group 1 salts** are soluble.\n"
            "* **Chlorides ($Cl^-$)** are soluble *except* Silver ($AgCl$) and Lead ($PbCl_2$).\n"
            "* **Sulphates ($SO_4^{2-}$)** are soluble *except* Barium ($BaSO_4$), Lead ($PbSO_4$), and Calcium ($CaSO_4$).\n"
            "* **Carbonates ($CO_3^{2-}$)** are insoluble *except* Sodium, Potassium, and Ammonium."
        )
        return reasoning, content

    # 3. Biology Topics
    if any(k in q for k in ["photosynthesis", "chlorophyll", "light reaction", "calvin"]):
        content = (
            "### Photosynthesis (Cameroon GCE Biology)\n\n"
            "Photosynthesis is the synthesis of organic glucose molecules from carbon dioxide "
            "and water using sunlight energy trapped by chlorophyll.\n\n"
            "$$6\\text{CO}_2 + 6\\text{H}_2\\text{O} \\xrightarrow[\\text{chlorophyll}]{\\text{sunlight}} \\text{C}_6\\text{H}_{12}\\text{O}_6 + 6\\text{O}_2$$\n\n"
            "**Two Major Stages:**\n"
            "1. **Light-Dependent Stage (Thylakoids):** Photolysis of water releases oxygen and produces ATP and NADPH.\n"
            "2. **Light-Independent Stage / Calvin Cycle (Stroma):** Carbon fixation incorporates CO₂ into carbohydrates."
        )
        return reasoning, content

    if any(k in q for k in ["cell", "mitochondria", "nucleus", "membrane"]):
        content = (
            "### Cell Structure & Organelles\n\n"
            "The cell is the basic structural and functional unit of living organisms.\n\n"
            "* **Nucleus:** Contains genetic DNA material; controls cellular activities.\n"
            "* **Mitochondria:** Site of aerobic cellular respiration; synthesizes ATP ('powerhouse').\n"
            "* **Cell Membrane:** Phospholipid bilayer regulating selective permeability.\n"
            "* **Chloroplast (Plants only):** Site of photosynthesis containing chlorophyll thylakoids.\n"
            "* **Cell Wall (Plants only):** Rigid cellulose structure providing mechanical support."
        )
        return reasoning, content

    # 4. Mathematics Topics
    if any(k in q for k in ["quadrat", "formula", "roots", "ax^2"]):
        content = (
            "### Quadratic Equations (Cameroon GCE Mathematics)\n\n"
            "For any quadratic equation in standard form:\n"
            "$$a x^2 + b x + c = 0 \\quad (a \\neq 0)$$\n\n"
            "**Quadratic Formula:**\n"
            "$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$\n\n"
            "**The Discriminant ($\\Delta = b^2 - 4ac$):**\n"
            "* If $\\Delta > 0$: Two distinct real roots.\n"
            "* If $\\Delta = 0$: Two equal (repeated) real roots.\n"
            "* If $\\Delta < 0$: No real roots (complex conjugates)."
        )
        return reasoning, content

    if any(k in q for k in ["calculus", "differentiat", "integrat", "derivative"]):
        content = (
            "### Differentiation & Calculus (GCE Advanced Level)\n\n"
            "**Power Rule:**\n"
            "$$\\frac{d}{dx}\\left[a x^n\\right] = a \\cdot n \\cdot x^{n-1}$$\n\n"
            "**Product & Quotient Rules:**\n"
            "* Product: $(uv)' = u'v + uv'$\n"
            "* Quotient: $\\left(\\frac{u}{v}\\right)' = \\frac{u'v - uv'}{v^2}$\n\n"
            "**Indefinite Integration:**\n"
            "$$\\int x^n \\, dx = \\frac{x^{n+1}}{n+1} + C \\quad (n \\neq -1)$$"
        )
        return reasoning, content

    # 5. Computer Science & ICT
    if any(k in q for k in ["binary", "logic gate", "algorithm", "python", "computer"]):
        content = (
            "### Binary & Logic Gates (Cameroon GCE Computer Science)\n\n"
            "Computers represent all instructions and data using the binary numeral system (base 2).\n\n"
            "**Primary Logic Gates:**\n"
            "* **AND Gate:** Output is 1 only when all inputs are 1 ($A \\cdot B$).\n"
            "* **OR Gate:** Output is 1 when at least one input is 1 ($A + B$).\n"
            "* **NOT Gate:** Inverts the single input ($\\overline{A}$).\n"
            "* **NAND / NOR:** Universal gates capable of constructing any logical circuit."
        )
        return reasoning, content

    # Default / General Question
    content = (
        f"### Fuserio AI Study Companion ({subj or 'Science & Math'})\n\n"
        f"I am ready to help you with your **{lvl}** studies!\n\n"
        f"**Question Analyzed:** *\"{query.strip()}\"*\n\n"
        "Here is the structured breakdown for your revision:\n\n"
        "1. **Core Syllabus Definition:** Formulate the precise scientific definition using standard GCE terminology.\n"
        "2. **Governing Principles & Equations:** Check the physical relationship or formula and note SI units.\n"
        "3. **Practical Application:** Connect the theory to our Virtual Pre-Lab experiments.\n\n"
        "> **Next Steps:** You can launch a virtual experiment from the **Virtual Practicals** folder, "
        "or ask me to give you an original past-paper-style practice question on this topic!"
    )
    return reasoning, content


def _detect_subject(query: str) -> str:
    physics_keywords = ["velocity", "force", "acceleration", "pendulum", "circuit", "ohm", "voltage", "current", "lens", "refraction", "gravity", "motion"]
    chemistry_keywords = ["acid", "base", "titrat", "salt", "reaction", "mole", "precipitat", "ph", "solubil", "catalyst", "electron"]
    bio_keywords = ["cell", "organ", "photosynthesis", "enzyme", "heart", "blood", "plant", "mitochondria", "respiration", "dna"]
    math_keywords = ["equation", "quadratic", "integral", "derivative", "trigonometry", "matrix", "vector", "probability"]
    cs_keywords = ["binary", "algorithm", "loop", "python", "code", "gate", "cpu", "memory"]

    for kw in physics_keywords:
        if kw in query:
            return "Physics"
    for kw in chemistry_keywords:
        if kw in query:
            return "Chemistry"
    for kw in bio_keywords:
        if kw in query:
            return "Biology"
    for kw in math_keywords:
        if kw in query:
            return "Mathematics"
    for kw in cs_keywords:
        if kw in query:
            return "Computer Science"
    return "Science"


detect_subject = _detect_subject
