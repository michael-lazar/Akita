from akita.display import Display


def test_display():
    """
    I haven't written any tests for this because mocking curses is hard.

    At least make sure we can import and instantiate the class.
    """
    assert Display(None)
