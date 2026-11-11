from scripts.capture_demo import progressive_reveals


def test_demo_answer_reveals_one_token_at_a_time():
    states = progressive_reveals("We calculate average speed.")

    assert states == [
        "We",
        "We calculate",
        "We calculate average",
        "We calculate average speed.",
    ]
    assert all(later.startswith(earlier) for earlier, later in zip(states, states[1:]))
