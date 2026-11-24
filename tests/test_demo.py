from scripts.capture_demo import progressive_reveals
from scripts.capture_showcase import ease_out_cubic


def test_demo_answer_reveals_one_token_at_a_time():
    states = progressive_reveals("We calculate average speed.")

    assert states == [
        "We",
        "We calculate",
        "We calculate average",
        "We calculate average speed.",
    ]
    assert all(later.startswith(earlier) for earlier, later in zip(states, states[1:]))


def test_showcase_easing_is_monotonic_and_finishes_at_destination():
    progress = [ease_out_cubic(step / 10) for step in range(11)]

    assert progress[0] == 0
    assert progress[-1] == 1
    assert progress == sorted(progress)
