import argparse
import os
import sys
import re
from collections import defaultdict

# Compile regex patterns once globally for efficiency
HEADER_PATTERN = re.compile(
    r"^\[\d{1,2}/\d{1,2}/\d{4},\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M\]\s+(.+?)\s*$"
)
DAMAGE_RECEIVED_PT = re.compile(r"^(.+?) recebe (\d+) de dano")
DAMAGE_RECEIVED_EN = re.compile(r"^(.+?) takes (\d+) damage")
HEALING_PT = re.compile(r"^(.+?) é curado em (\d+) de dano")
HEALING_EN = re.compile(r"^(.+?) is healed for (\d+) damage")
ROLL_RESULT_PATTERN = re.compile(r"^.+ = (\d+) = \d+$")
ROLL_HEALING = re.compile(r"^Roll Healing")
DAMAGE_TYPE_PATTERN = re.compile(
    r"\b(bludgeoning|piercing|slashing|poison|fire|cold|electricity|acid|sonic|mental|vitality|void|force|spirit)\b"
)
PHYSICAL_DAMAGE_TYPES = {"bludgeoning", "piercing", "slashing", "poison"}

def parse_log_line(line, current_player=None):
    """
    Parses a single line from the Foundry log file to extract relevant event data.

    Args:
        line (str): The log line to parse.
        current_player (str | None): The name of the player who sent the current
                                     message block (from the preceding header line).

    Returns:
        dict or None: A dictionary with event data, or None if the line does not
                      match any known event pattern.
    """
    if match := DAMAGE_RECEIVED_PT.match(line):
        target, value = match.groups()
        return {'type': 'damage_received', 'target': target, 'value': int(value)}

    if match := DAMAGE_RECEIVED_EN.match(line):
        target, value = match.groups()
        return {'type': 'damage_received', 'target': target, 'value': int(value)}

    if match := HEALING_PT.match(line):
        target, value = match.groups()
        source = current_player if current_player else target
        return {'type': 'healing', 'source': source, 'target': target, 'value': int(value)}

    if match := HEALING_EN.match(line):
        target, value = match.groups()
        source = current_player if current_player else target
        return {'type': 'healing', 'source': source, 'target': target, 'value': int(value)}

    if current_player and (match := ROLL_RESULT_PATTERN.match(line)):
        value = int(match.group(1))
        damage_type_match = DAMAGE_TYPE_PATTERN.search(line)
        if damage_type_match:
            damage_type = damage_type_match.group(1)
            category = 'physical' if damage_type in PHYSICAL_DAMAGE_TYPES else 'magical'
            return {
                'type': 'damage_caused',
                'source': current_player,
                'value': value,
                'damage_type': category,
            }

    return None

def aggregate_stats(events):
    """
    Aggregates raw parsed events to calculate total damage caused,
    damage received, and healing done per character.

    Args:
        events (list): A list of dictionaries, where each dictionary
                       represents a parsed log event.

    Returns:
        dict: A dictionary where keys are character names and values are
              dictionaries containing their aggregated statistics.
    """
    character_stats = defaultdict(lambda: {
        'damage_caused_physical': 0,
        'damage_caused_magical': 0,
        'damage_received': 0,
        'healing': 0
    })

    for event in events:
        event_type = event['type']

        if event_type == 'damage_received':
            target = event['target']
            value = event['value']
            character_stats[target]['damage_received'] += value
        elif event_type == 'damage_caused':
            source = event['source']
            value = event['value']
            damage_type = event['damage_type']
            if damage_type == 'physical':
                character_stats[source]['damage_caused_physical'] += value
            elif damage_type == 'magical':
                character_stats[source]['damage_caused_magical'] += value
        elif event_type == 'healing':
            source = event['source']
            value = event['value']
            character_stats[source]['healing'] += value
    return character_stats

def get_player_from_header(line):
    """
    Returns the player name if the line is a message header, None otherwise.

    Header format: [M/D/YYYY, H:MM:SS AM/PM] PlayerName
    """
    match = HEADER_PATTERN.match(line)
    return match.group(1) if match else None

def parse_log_file(file_path):
    """
    Parses a Foundry log file and returns a list of events.

    Args:
        file_path (str): Path to the Foundry log file.

    Returns:
        list: A list of event dictionaries with keys: type, source/target, value, damage_type, timestamp.
    """
    from datetime import datetime

    with open(file_path, 'r', encoding='utf-8') as f:
        events = []
        current_player = None
        healer_context = None  # Track who is casting a healing spell

        for line in f:
            line = line.strip()
            player = get_player_from_header(line)
            if player:
                current_player = player
                continue

            # Check if this is a healing spell roll (sets healer context)
            if ROLL_HEALING.match(line):
                healer_context = current_player
                events.append({'type': 'timestamp', 'timestamp': '', 'player': current_player})
                continue

            event = parse_log_line(line, current_player)
            if event:
                # For healing events, use healer_context as source if available
                if event['type'] == 'healing' and healer_context:
                    event['source'] = healer_context
                events.append(event)

                # Reset healer context after processing heal event (only once per spell)
                if event['type'] == 'healing':
                    healer_context = None

        return events

def main():
    """
    Main function to parse command-line arguments, read the log file,
    aggregate statistics, and print the formatted summary.
    """
    parser = argparse.ArgumentParser(description="Analyze Foundry log files.")
    parser.add_argument("log_file", help="Path to the Foundry log file.")
    args = parser.parse_args()

    log_file_path = args.log_file

    if not os.path.exists(log_file_path):
        print(f"Error: The file '{log_file_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(log_file_path):
        print(f"Error: '{log_file_path}' is not a file.", file=sys.stderr)
        sys.exit(1)

    if not os.access(log_file_path, os.R_OK):
        print(f"Error: The file '{log_file_path}' is not readable. Check permissions.", file=sys.stderr)
        sys.exit(1)

    print(f"Successfully validated log file: {log_file_path}")

    events = parse_log_file(log_file_path)

    character_stats = aggregate_stats(events)
    print("\nResumo da Sessão:")
    print("-----------------")
    print()

    for character, stats in character_stats.items():
        print(f"Personagem {character}:")
        print(f"  - Dano Causado:")
        print(f"    - Físico: {stats['damage_caused_physical']}")
        print(f"    - Mágico: {stats['damage_caused_magical']}")
        print(f"  - Dano Recebido: {stats['damage_received']}")
        print(f"  - Cura Realizada: {stats['healing']}")
        print()

if __name__ == "__main__":
    main()
