from localchat.lab_data import (
    EXPERIMENTS,
    MODEL_EQUATIONS,
    MODEL_LIMITATIONS,
    SUBJECTS,
    experiment_by_id,
    experiments_for_subject,
    model_equation,
    model_limitation,
)


def test_catalog_covers_all_requested_subjects_with_multiple_experiments():
    assert SUBJECTS == ("Physics", "Biology", "Chemistry")
    assert all(len(experiments_for_subject(subject)) >= 2 for subject in SUBJECTS)


def test_experiment_ids_are_unique_and_every_experiment_has_learning_and_safety_text():
    identifiers = [experiment.identifier for experiment in EXPERIMENTS]

    assert len(identifiers) == len(set(identifiers))
    assert all(experiment.objective.strip() for experiment in EXPERIMENTS)
    assert all(experiment.safety.strip() for experiment in EXPERIMENTS)
    assert all(experiment.parameters for experiment in EXPERIMENTS)


def test_experiment_lookup_and_subject_filter_are_consistent():
    pendulum = experiment_by_id("pendulum-lab")

    assert pendulum is not None
    assert pendulum.subject == "Physics"
    assert pendulum in experiments_for_subject("Physics")
    assert experiment_by_id("unknown-lab") is None


def test_each_experiment_has_a_relationship_and_limit_note():
    identifiers = {experiment.identifier for experiment in EXPERIMENTS}

    assert set(MODEL_EQUATIONS) == identifiers
    assert set(MODEL_LIMITATIONS) == identifiers
    assert all(model_equation(identifier) for identifier in identifiers)
    assert all(model_limitation(identifier) for identifier in identifiers)
