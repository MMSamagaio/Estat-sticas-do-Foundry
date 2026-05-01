import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from foundry_log_analyzer import parse_log_line, get_player_from_header, aggregate_stats

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
        assert result == {'type': 'healing', 'source': 'Lewys//Moja', 'target': 'Lewys//Moja', 'value': 5}

    def test_portuguese_multiword_name(self):
        result = parse_log_line("Gezras Aep Fin Dabair é curado em 8 de dano.", current_player=None)
        assert result == {'type': 'healing', 'source': 'Gezras Aep Fin Dabair', 'target': 'Gezras Aep Fin Dabair', 'value': 8}

    def test_english(self):
        result = parse_log_line("Jobu is healed for 3 damage.", current_player=None)
        assert result == {'type': 'healing', 'source': 'Jobu', 'target': 'Jobu', 'value': 3}

    def test_no_match_returns_none(self):
        result = parse_log_line("{Game Time: }", current_player=None)
        assert result is None

class TestDamageCaused:
    def test_physical_bludgeoning(self):
        result = parse_log_line("2d4 bludgeoning = 8 = 8", current_player="Lewys//Moja")
        assert result == {
            'type': 'damage_caused',
            'source': 'Lewys//Moja',
            'value': 8,
            'damage_type': 'physical',
        }

    def test_physical_piercing(self):
        result = parse_log_line("1d8 piercing = 5 = 5", current_player="Mayk")
        assert result == {
            'type': 'damage_caused',
            'source': 'Mayk',
            'value': 5,
            'damage_type': 'physical',
        }

    def test_physical_complex_expression(self):
        result = parse_log_line("2 * (1d6 + 3) + 1d8 slashing = 16 = 16", current_player="MAiron")
        assert result == {
            'type': 'damage_caused',
            'source': 'MAiron',
            'value': 16,
            'damage_type': 'physical',
        }

    def test_magical_acid(self):
        result = parse_log_line("4d6 acid = 13 = 13", current_player="Mario")
        assert result == {
            'type': 'damage_caused',
            'source': 'Mario',
            'value': 13,
            'damage_type': 'magical',
        }

    def test_magical_vitality(self):
        result = parse_log_line("1d8 vitality = 7 = 7", current_player="Lewys//Moja")
        assert result == {
            'type': 'damage_caused',
            'source': 'Lewys//Moja',
            'value': 7,
            'damage_type': 'magical',
        }

    def test_attack_roll_ignored(self):
        # 1d20 has the = N = N format but no damage type → must be ignored
        result = parse_log_line("1d20 = 4 = 4", current_player="MAiron")
        assert result is None

    def test_untyped_roll_ignored(self):
        # Roll without explicit damage type → ignore
        result = parse_log_line("1d8 = 5 = 5", current_player="Lewys//Moja")
        assert result is None

    def test_no_player_context_ignored(self):
        # No player context → ignore roll
        result = parse_log_line("1d8 piercing = 5 = 5", current_player=None)
        assert result is None


class TestGetPlayerFromHeader:
    def test_detects_header(self):
        assert get_player_from_header("[5/25/2024, 11:08:53 PM] Lewys//Moja") == "Lewys//Moja"

    def test_detects_header_multiword(self):
        assert get_player_from_header("[5/25/2024, 10:53:40 PM] Mario") == "Mario"

    def test_non_header_returns_none(self):
        assert get_player_from_header("MAiron recebe 3 de dano.") is None

    def test_game_time_line_returns_none(self):
        assert get_player_from_header("{Game Time: }") is None


class TestAggregateStats:
    def test_aggregates_damage_received(self):
        events = [
            {'type': 'damage_received', 'target': 'MAiron', 'value': 3},
            {'type': 'damage_received', 'target': 'MAiron', 'value': 1},
        ]
        stats = aggregate_stats(events)
        assert stats['MAiron']['damage_received'] == 4

    def test_aggregates_healing(self):
        events = [
            {'type': 'healing', 'source': 'Mayk', 'target': 'Lewys//Moja', 'value': 5},
            {'type': 'healing', 'source': 'Mayk', 'target': 'Lewys//Moja', 'value': 3},
        ]
        stats = aggregate_stats(events)
        assert stats['Mayk']['healing'] == 8

    def test_aggregates_physical_damage_caused(self):
        events = [
            {'type': 'damage_caused', 'source': 'Mayk', 'value': 7, 'damage_type': 'physical'},
            {'type': 'damage_caused', 'source': 'Mayk', 'value': 8, 'damage_type': 'physical'},
        ]
        stats = aggregate_stats(events)
        assert stats['Mayk']['damage_caused_physical'] == 15

    def test_aggregates_magical_damage_caused(self):
        events = [
            {'type': 'damage_caused', 'source': 'Mario', 'value': 13, 'damage_type': 'magical'},
        ]
        stats = aggregate_stats(events)
        assert stats['Mario']['damage_caused_magical'] == 13
