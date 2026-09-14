from lunaengine.backend.transition import Transition, TransitionType


def test_transition_normalizes_duration_and_eases_progress():
    transition = Transition(None, None, TransitionType.FADE, duration=-2)
    assert transition.duration == 0.0

    transition.progress = 0.5
    assert transition.eased_progress == 0.5

    transition.progress = 4.0
    assert transition.eased_progress == 1.0
