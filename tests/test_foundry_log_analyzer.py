import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from foundry_log_analyzer import parse_log_line

class TestDamageReceived:
    def test_portuguese_simple(self):
        result = parse_log_line("MAiron recebe 3 de dano.", current_player=None)
        assert result == {'type': 'damage_received', 'target': 'MAiron', 'value': 3}

    def test_portuguese_with_trailing_text(self):
        result = parse_log_line("Goblin Warrior recebe 15 de dano. O dano maciço o mata imediatamente.", current_player=None)
        assert result == {'type': 'damage_received', 'target': 'Goblin Warrior', 'value': 15}

    def test_portuguese_special_chars_in_name(self):
        result = parse_log_line("Lewys//Moja recebe 10 de dano.", current_player=None)
        assert result == {'type': 'damage_received', 'target': 'Lewys//Moja', 'value': 10}

    def test_portuguese_accented_name(self):
        result = parse_log_line("Óskima recebe 2 de dano.", current_player=None)
        assert result == {'type': 'damage_received', 'target': 'Óskima', 'value': 2}

    def test_portuguese_multiword_name(self):
        result = parse_log_line("Gezras Aep Fin Dabair recebe 16 de dano.", current_player=None)
        assert result == {'type': 'damage_received', 'target': 'Gezras Aep Fin Dabair', 'value': 16}

    def test_english(self):
        result = parse_log_line("Mayk takes 2 damage.", current_player=None)
        assert result == {'type': 'damage_received', 'target': 'Mayk', 'value': 2}

    def test_no_match_returns_none(self):
        result = parse_log_line("Timber 2 Cantrip ...", current_player=None)
        assert result is None

class TestHealing:
    def test_portuguese_simple(self):
        result = parse_log_line("Lewys//Moja é curado em 5 de dano.", current_player=None)
        assert result == {'type': 'healing', 'target': 'Lewys//Moja', 'value': 5}

    def test_portuguese_multiword_name(self):
        result = parse_log_line("Gezras Aep Fin Dabair é curado em 8 de dano.", current_player=None)
        assert result == {'type': 'healing', 'target': 'Gezras Aep Fin Dabair', 'value': 8}

    def test_english(self):
        result = parse_log_line("Jobu is healed for 3 damage.", current_player=None)
        assert result == {'type': 'healing', 'target': 'Jobu', 'value': 3}

    def test_no_match_returns_none(self):
        result = parse_log_line("{Game Time: }", current_player=None)
        assert result is None
