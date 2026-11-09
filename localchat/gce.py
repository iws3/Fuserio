import json
import os
from typing import Any


SUBJECTS: dict[str, dict[str, list[str]]] = {
    "Ordinary Level": {
        "Sciences": [
            "Mathematics",
            "Additional Mathematics",
            "Physics",
            "Chemistry",
            "Biology",
            "Human Biology",
            "Computer Science",
            "ICT",
            "Agricultural Science",
            "Food and Nutrition",
            "Physical Education",
        ],
        "Arts": [
            "Literature in English",
            "History",
            "Geography",
            "Citizenship Education",
            "Religious Studies",
            "Logic",
            "Philosophy",
            "Art",
            "Music",
        ],
        "Languages": ["English Language", "French", "German", "Spanish"],
        "Commercial": [
            "Economics",
            "Commerce",
            "Accounting",
            "Business Mathematics",
            "Technical Drawing",
        ],
    },
    "Advanced Level": {
        "Sciences": [
            "Pure Mathematics with Mechanics",
            "Further Mathematics",
            "Physics",
            "Chemistry",
            "Biology",
            "Computer Science",
            "Geology",
            "ICT",
            "Food Science and Nutrition",
        ],
        "Arts": [
            "Literature in English",
            "History",
            "Geography",
            "Philosophy",
            "Logic",
            "Religious Studies",
            "Law",
            "Education",
            "Art",
            "Music",
        ],
        "Languages": ["English Language", "French", "German", "Spanish"],
        "Commercial": ["Economics", "Accounting", "Management in Living"],
    },
}

STREAMS = ("Sciences", "Arts", "Languages", "Commercial")
LEARNING_MODES = ("Lesson", "Practice", "Past-paper quiz", "Ask a question")

_FULL_WORKING_SUBJECTS = {
    "Mathematics",
    "Additional Mathematics",
    "Business Mathematics",
    "Pure Mathematics with Mechanics",
    "Further Mathematics",
    "Physics",
    "Chemistry",
    "Accounting",
}

_TOPIC_SCAFFOLDS = {
    "Mathematics": ("Number and calculation", "Algebra and graphs", "Geometry and mensuration", "Statistics and probability"),
    "Additional Mathematics": ("Algebra and functions", "Coordinate geometry", "Trigonometry", "Calculus and vectors"),
    "Business Mathematics": ("Number skills and ratios", "Percentages and interest", "Commercial arithmetic", "Statistics and graphs"),
    "Pure Mathematics with Mechanics": ("Functions and algebra", "Differentiation and integration", "Vectors and coordinate geometry", "Forces and motion"),
    "Further Mathematics": ("Advanced algebra and functions", "Calculus", "Vectors and matrices", "Mechanics and modelling"),
    "Physics": ("Measurement and physical quantities", "Motion, forces and energy", "Properties of matter and waves", "Electricity and magnetism"),
    "Chemistry": ("Particles, atoms and bonding", "Formulae and chemical equations", "Acids, bases and salts", "Rates, energy and organic chemistry"),
    "Biology": ("Cells and organization", "Nutrition and transport", "Respiration and excretion", "Reproduction, inheritance and ecology"),
    "Human Biology": ("Cells, tissues and organs", "Nutrition and digestion", "Circulation and respiration", "Reproduction, health and homeostasis"),
    "Accounting": ("Source documents and books of original entry", "Double entry and ledger accounts", "Trial balance and error correction", "Financial statements and interpretation"),
    "Economics": ("Scarcity and choice", "Demand, supply and markets", "Production and distribution", "Money, trade and development"),
    "Commerce": ("Trade and business organization", "Buying, selling and distribution", "Transport, communication and insurance", "Banking and international trade"),
    "Geography": ("Map skills and geographical methods", "Physical environments and processes", "Population and settlement", "Economic activities and sustainability"),
    "History": ("Working with historical sources", "Societies and change over time", "Colonialism and resistance", "Cameroon, independence and nation-building"),
    "Literature in English": ("Close reading and interpretation", "Poetry: voice, imagery and form", "Prose: character, setting and theme", "Drama and essay writing"),
    "English Language": ("Comprehension and summary", "Grammar and sentence structure", "Vocabulary and register", "Composition and communication"),
    "French": ("Compréhension et résumé", "Grammaire et conjugaison", "Vocabulaire et expression", "Rédaction et communication"),
}


def suggested_topic_areas(level: str, stream: str, subject: str) -> tuple[str, ...]:
    if subject not in SUBJECTS.get(level, {}).get(stream, []):
        raise ValueError(f"{subject!r} is not listed for {level} {stream}.")
    if subject in _TOPIC_SCAFFOLDS:
        return _TOPIC_SCAFFOLDS[subject]
    return (
        f"Key terms and foundations in {subject}",
        f"Core concepts and principles in {subject}",
        f"Methods, evidence and applications in {subject}",
        f"Cameroon-focused examples and exam skills in {subject}",
    )


def build_tutor_system_prompt(level: str, stream: str, subject: str) -> str:
    if subject not in SUBJECTS.get(level, {}).get(stream, []):
        raise ValueError(f"{subject!r} is not listed for {level} {stream}.")

    level_guidance = (
        "Use simple, clear, step-by-step explanations suitable for O Level. "
        "Introduce one idea at a time and check understanding."
        if level == "Ordinary Level"
        else "Use deeper analysis suitable for A Level. Explain assumptions, connections, "
        "and why each method is valid while keeping the reasoning accessible."
    )
    working_guidance = (
        "For calculations, show every formula, substitution, intermediate step, unit, "
        "and final answer. Never skip working."
        if subject in _FULL_WORKING_SUBJECTS
        else "Show clear reasoning and organize answers in the form expected by the exam."
    )
    topic_menu = "\n".join(
        f"{index}. {topic}"
        for index, topic in enumerate(suggested_topic_areas(level, stream, subject), start=1)
    )
    return "\n".join(
        (
            "You are a patient tutor helping a student prepare for the Cameroon GCE Board.",
            f"The student's level is {level}; stream is {stream}; selected subject is {subject}.",
            "Stay within this exact subject and level. Do not drift into unrelated subjects or another level.",
            "Follow the Cameroon GCE Board syllabus and exam marking style. The app only has subject names, "
            "not an authoritative topic-by-topic syllabus. Use syllabus topics only when you are confident; "
            "if exact official coverage or a past-paper detail is uncertain, say so plainly and ask the student "
            "to share their teacher's or Board's topic list instead of inventing it.",
            "Start with a greeting and the following topic-menu scaffold. Label it 'Suggested study areas, "
            "not a verified or exhaustive official syllabus'. It is a starting point for choosing a topic; "
            "say when an area may not match the current Board syllabus.",
            topic_menu,
            level_guidance,
            working_guidance,
            "Use familiar Cameroonian examples when useful, such as CFA francs, markets, farms, transport, "
            "weather, local geography, or community life. Keep examples respectful and realistic.",
            "When the student answers an exercise, mark it against clear steps or marks, explain any errors, "
            "and provide a complete model answer.",
            "At the start of a new subject chat, greet the student, present a concise numbered menu of "
            "syllabus topics for this subject, and offer these choices: Lesson, Practice, Past-paper quiz, "
            "or Ask a question. Invite the student to choose a topic or mode.",
            "For past-paper quizzes, create original past-paper-style questions unless the student supplies "
            "a question. Never claim an invented question is an official past-paper question.",
            "Use plain language, supportive tone, and well-structured answers. Be honest whenever unsure.",
        )
    )


def default_progress() -> dict[str, Any]:
    return {"selection": {}, "sessions": {}}


def progress_path() -> str:
    return os.path.join(os.path.expanduser("~/.local/share/localchat"), "gce-progress.json")


def load_progress(path: str | None = None) -> dict[str, Any]:
    try:
        with open(path or progress_path(), encoding="utf-8") as progress_file:
            data = json.load(progress_file)
    except (OSError, json.JSONDecodeError):
        return default_progress()

    if not isinstance(data, dict):
        return default_progress()
    if not isinstance(data.get("selection"), dict):
        data["selection"] = {}
    if not isinstance(data.get("sessions"), dict):
        data["sessions"] = {}
    return data


def save_progress(progress: dict[str, Any], path: str | None = None) -> None:
    destination = path or progress_path()
    os.makedirs(os.path.dirname(destination) or ".", exist_ok=True)
    temporary_path = f"{destination}.tmp"
    with open(temporary_path, "w", encoding="utf-8") as progress_file:
        json.dump(progress, progress_file, ensure_ascii=False, indent=2)
    os.replace(temporary_path, destination)