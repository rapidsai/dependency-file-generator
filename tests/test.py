from unittest.mock import patch
import os.path


def my_isfile(filename):
    """Test function which calls os.path.isfile"""
    if os.path.isfile(filename):
        return "Yes"
    else:
        return "Wrong"


@patch("os.path.isfile")
def test_isfile_with_return_value(mock_isfile):
    """Mocking os.path.isfile and using return_value"""
    mock_isfile.return_value = True
    assert my_isfile("bla") == "Yes"


@patch("os.path.isfile")
def test_isfile_with_side_effects(mock_isfile):
    """Mocking os.path.isfile with using side_effect"""

    def side_effect(filename):
        if filename == "foo":
            return True
        else:
            return False

    mock_isfile.side_effect = side_effect
    assert my_isfile("foo") == "Yes"
    assert my_isfile("bla") == "Wrong"
