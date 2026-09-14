from lunaengine.backend.transition import TransitionType


def test_transition_types_are_public_and_complete():
    assert TransitionType.ZOOM_IN.name == "ZOOM_IN"
    assert TransitionType.ORBITAL_LEFT.name == "ORBITAL_LEFT"
    assert TransitionType.ORBITAL_RIGHT.name == "ORBITAL_RIGHT"
    assert TransitionType.MORPH.name == "MORPH"
    assert TransitionType.FLASH.name == "FLASH"
