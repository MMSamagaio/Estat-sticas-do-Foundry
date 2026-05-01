import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui import create_window, parse_and_display

class TestCreateWindow:
    def test_window_created(self):
        window = create_window()
        assert window is not None
        window.close()

    def test_window_has_title(self):
        window = create_window()
        assert window.Title == "Foundry Log Analyzer"
        window.close()

class TestParseAndDisplay:
    # Tests for parse_and_display using a sample log file
    pass