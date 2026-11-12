from dataclasses import dataclass


@dataclass(frozen=True)
class LabParameter:
    key: str
    label: str
    minimum: int
    maximum: int
    value: int
    unit: str


@dataclass(frozen=True)
class Experiment:
    identifier: str
    subject: str
    title: str
    subtitle: str
    description: str
    objective: str
    safety: str
    parameters: tuple[LabParameter, ...]


EXPERIMENTS = (
    Experiment(
        identifier="projectile-motion",
        subject="Physics",
        title="Projectile motion",
        subtitle="Launch, trace, measure",
        description="Explore how launch speed and angle shape the path of a ball under gravity.",
        objective="Compare horizontal range, maximum height and flight time as you change the launch angle.",
        safety="Simulation only. Real projectiles can injure people; never test launches toward people, roads or property.",
        parameters=(
            LabParameter("angle", "Launch angle", 10, 80, 45, "°"),
            LabParameter("speed", "Launch speed", 10, 40, 25, "m/s"),
            LabParameter("gravity", "Gravity", 2, 20, 10, "m/s²"),
        ),
    ),
    Experiment(
        identifier="pendulum-lab",
        subject="Physics",
        title="Pendulum lab",
        subtitle="Length changes the rhythm",
        description="Release a pendulum and compare its period as its length or starting angle changes.",
        objective="Observe that a longer pendulum swings more slowly and estimate its period.",
        safety="Simulation only. Secure any real pendulum and keep swinging masses away from faces and fragile items.",
        parameters=(
            LabParameter("length", "String length", 30, 180, 100, "cm"),
            LabParameter("angle", "Release angle", 5, 50, 25, "°"),
            LabParameter("damping", "Air resistance", 0, 30, 4, "%"),
        ),
    ),
    Experiment(
        identifier="ohms-law",
        subject="Physics",
        title="Ohm's law circuit",
        subtitle="Voltage, resistance, current",
        description="Build a simple circuit model and see how voltage and resistance affect current.",
        objective="Use V = IR to predict current, then compare your prediction with the meter.",
        safety="Low-voltage simulation. Do not copy circuit experiments using mains electricity or unknown power supplies.",
        parameters=(
            LabParameter("voltage", "Voltage", 1, 24, 12, "V"),
            LabParameter("resistance", "Resistance", 2, 48, 12, "Ω"),
        ),
    ),
    Experiment(
        identifier="diffusion",
        subject="Biology",
        title="Membrane diffusion",
        subtitle="Concentration finds a balance",
        description="Watch particles move across a permeable membrane from high concentration to low concentration.",
        objective="Relate net movement to the concentration gradient and membrane permeability.",
        safety="Computer model only. It does not replace laboratory procedures for handling biological samples.",
        parameters=(
            LabParameter("gradient", "Concentration gradient", 10, 90, 70, "%"),
            LabParameter("permeability", "Membrane permeability", 0, 100, 55, "%"),
        ),
    ),
    Experiment(
        identifier="enzyme-activity",
        subject="Biology",
        title="Enzyme activity",
        subtitle="Temperature and reaction rate",
        description="Explore how temperature changes enzyme-substrate collisions in a simplified model.",
        objective="Identify the difference between faster collisions and loss of enzyme activity at high temperature.",
        safety="Illustrative model only. It is not a measurement of a real enzyme or a clinical prediction.",
        parameters=(
            LabParameter("temperature", "Temperature", 5, 90, 37, "°C"),
            LabParameter("enzyme", "Enzyme concentration", 1, 10, 5, "units"),
        ),
    ),
    Experiment(
        identifier="natural-selection",
        subject="Biology",
        title="Natural selection",
        subtitle="Variation meets environment",
        description="Change the environment and observe how inherited variation can shift a population over generations.",
        objective="Track how selection pressure changes trait frequency while variation remains in a population.",
        safety="A simplified population model, not a prediction for any real community or ecosystem.",
        parameters=(
            LabParameter("pressure", "Selection pressure", 0, 100, 55, "%"),
            LabParameter("variation", "Trait variation", 1, 100, 45, "%"),
            LabParameter("generations", "Generations", 1, 40, 20, ""),
        ),
    ),
    Experiment(
        identifier="reaction-rate",
        subject="Chemistry",
        title="Reaction rate",
        subtitle="Temperature changes collisions",
        description="Adjust particle energy and concentration to see how often effective collisions occur.",
        objective="Connect collision frequency and energy to the rate of a chemical reaction.",
        safety="Particle model only. Do not mix chemicals outside a supervised, properly equipped laboratory.",
        parameters=(
            LabParameter("temperature", "Temperature", 10, 100, 40, "°C"),
            LabParameter("concentration", "Concentration", 10, 100, 55, "%"),
        ),
    ),
    Experiment(
        identifier="titration",
        subject="Chemistry",
        title="Acid-base titration",
        subtitle="Find the endpoint carefully",
        description="Add titrant in measured steps and observe an indicator color change near the endpoint.",
        objective="Read the burette volume and distinguish a gradual pH change from the endpoint region.",
        safety="Model only. Real acids and bases require teacher supervision, goggles and proper disposal.",
        parameters=(
            LabParameter("volume", "Titrant added", 0, 50, 0, "mL"),
            LabParameter("concentration", "Titrant concentration", 10, 100, 50, "%"),
        ),
    ),
    Experiment(
        identifier="particle-states",
        subject="Chemistry",
        title="States of matter",
        subtitle="Heat the particle model",
        description="Change temperature and particle attraction to compare solid, liquid and gas-like motion.",
        objective="Relate particle kinetic energy and spacing to observable properties of each state.",
        safety="Particle model only; the display is not to scale and does not show real molecular forces in full.",
        parameters=(
            LabParameter("temperature", "Temperature", 0, 100, 35, "°C"),
            LabParameter("attraction", "Particle attraction", 0, 100, 60, "%"),
        ),
    ),
)

SUBJECTS = ("Physics", "Biology", "Chemistry")

MODEL_EQUATIONS = {
    "projectile-motion": r"$x = u\cos\theta\,t$  ·  $y = u\sin\theta\,t - \frac{1}{2}gt^2$",
    "pendulum-lab": r"$T \approx 2\pi\sqrt{\frac{L}{g}}$  ·  small-angle model",
    "ohms-law": r"$V = IR$  ·  $P = VI$",
    "diffusion": r"$J = -D\,\frac{\Delta C}{\Delta x}$  ·  concentration gradient",
    "enzyme-activity": r"$\text{rate} \propto [E]$  ·  simplified temperature response",
    "natural-selection": r"$p_{n+1}$ depends on trait fitness and $p_n$  ·  population model",
    "reaction-rate": r"$\text{rate} \propto$ effective collision frequency",
    "titration": r"$\text{pH} = -\log_{10}[H^+]$  ·  indicator changes near the endpoint",
    "particle-states": r"$\overline{E_k} \propto T$  ·  particle motion model",
}

MODEL_LIMITATIONS = {
    "projectile-motion": "Assumes a level launch and landing, constant gravity, and no air resistance.",
    "pendulum-lab": "The displayed period formula is an approximation for small angles; damping is illustrative.",
    "ohms-law": "Assumes a steady ideal circuit and an ohmic resistor whose resistance does not heat up.",
    "diffusion": "Uses a simplified concentration-gradient model; real membranes have selective transport and active processes.",
    "enzyme-activity": "Shows a simplified optimum curve; actual enzymes have different optimum conditions and kinetics.",
    "natural-selection": "Illustrates one trait under selection; real populations have many interacting traits and forces.",
    "reaction-rate": "Collision dots are illustrative; the model does not resolve molecular structure or activation energy distributions.",
    "titration": "Uses an illustrative endpoint curve; accurate pH depends on the actual acid, base, and concentrations.",
    "particle-states": "Particles are not to scale and the drawing simplifies real intermolecular forces and motion.",
}


def experiments_for_subject(subject: str) -> tuple[Experiment, ...]:
    return tuple(experiment for experiment in EXPERIMENTS if experiment.subject == subject)


def experiment_by_id(identifier: str) -> Experiment | None:
    return next((experiment for experiment in EXPERIMENTS if experiment.identifier == identifier), None)


def model_equation(identifier: str) -> str:
    return MODEL_EQUATIONS.get(identifier, "Qualitative model; compare variables and observed trends.")


def model_limitation(identifier: str) -> str:
    return MODEL_LIMITATIONS.get(identifier, "This is a simplified model, not an exact measurement of a real experiment.")
