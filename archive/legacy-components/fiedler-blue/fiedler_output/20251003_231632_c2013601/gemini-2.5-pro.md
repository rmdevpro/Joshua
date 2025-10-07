```python
import csv
import re
import os

# --- Constants and Configuration ---
INPUT_FILE = 'all_conversations_concat.txt'
OUTPUT_FILE = 'parsed_conversations.csv'
BASE_SOURCE_PATH = '/mnt/projects/ICCM/conversation_backups/consolidated/'
CSV_HEADER = ['filename', 'turn_number', 'role', 'content', 'timestamp', 'source_file']

# --- Regex Patterns for Turn Detection ---
# Order matters: more specific patterns should come first.
TURN_PATTERNS = [
    # User roles
    (r'^> ?(.*)', 'user'),
    (r'^User: ?(.*)', 'user'),
    (r'^(?:Human|User) to Gemini: ?(.*)', 'user'),
    (r'^### Initial Analysis Request:.*', 'user'),

    # Assistant roles
    (r'^● ?(.*)', 'assistant'),
    (r'^Assistant: ?(.*)', 'assistant'),
    (r'^A: ?(.*)', 'assistant'),
    (r'^Gemini Response: ?(.*)', 'assistant'),

    # Tool role
    (r'^⎿ ?(.*)', 'tool'),

    # System roles (often single-line markers that define a turn boundary)
    (r'^(▐▛███▜▌.*)', 'system'),
    (r'^(CHAT SESSION STARTED.*)', 'system'),
    (r'^(CHAT BACKUP.*)', 'system'),
    (r'^(--- Exchange \d+.*)', 'system'),
    (r'^(# .*Session Summary.*)', 'system'),
    (r'^(═════════.*)', 'system'),
    (r'^(──────────.*)', 'system'),
    (r'^(╭───.*)', 'system'),
    (r'^(╰───.*)', 'system'),
    (r'^(⏵⏵ .*?)$', 'system'),
]

def parse_conversations(input_path, output_path):
    """
    Parses the concatenated conversation file and writes to a CSV.
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            full_content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}")
        # Create an empty output file with headers
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            writer.writerow(CSV_HEADER)
        return

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        writer.writerow(CSV_HEADER)

        # Split content by file headers using a regex that captures the filename
        file_blocks = re.split(r'\n=== FILE: (.+?) ===\n', full_content)
        
        if len(file_blocks) > 1:
            # file_blocks will be ['', filename1, content1, filename2, content2, ...]
            # We iterate over pairs of (filename, content)
            for i in range(1, len(file_blocks), 2):
                filename = file_blocks[i].strip()
                content = file_blocks[i+1]
                process_single_file(filename, content, writer)

def process_single_file(filename, content, writer):
    """
    Processes the content of a single file and writes its turns to the CSV.
    """
    source_file = os.path.join(BASE_SOURCE_PATH, filename)
    
    # State for the parser
    turns = []
    current_turn = None
    last_timestamp = None
    
    # Extract a global timestamp from file headers if available
    header_ts_match = re.search(r'(?:CHAT SESSION STARTED|CHAT BACKUP) - (\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})', content)
    if header_ts_match:
        date_part = header_ts_match.group(1)
        time_part = header_ts_match.group(2).replace('-', ':')
        last_timestamp = f"{date_part} {time_part}"

    lines = content.split('\n')

    for line in lines:
        # --- Timestamp Extraction ---
        ts_match = re.search(r'\((\d{2}:\d{2}:\d{2})\)', line) or \
                   re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line) or \
                   re.search(r'--- (\d{2}:\d{2}:\d{2}) ---', line)
        if ts_match:
            time_str = ts_match.groups()[0].replace('-', ':')
            if ' ' in time_str: # Full timestamp
                last_timestamp = time_str
            elif last_timestamp and ' ' in last_timestamp: # Only time, but we have a date
                date_part = last_timestamp.split(' ')[0]
                last_timestamp = f"{date_part} {time_str}"
            else: # Only time, no date context
                last_timestamp = time_str

        # --- Turn Detection ---
        new_role = None
        cleaned_line = line
        
        for pattern, role in TURN_PATTERNS:
            match = re.match(pattern, line)
            if match:
                new_role = role
                cleaned_line = match.group(1).strip() if match.groups() and match.group(1) is not None else line.strip()
                break

        # --- State Machine Logic ---
        if new_role:
            if current_turn:
                turns.append(current_turn)
            
            current_turn = {
                'role': new_role,
                'content': [cleaned_line] if cleaned_line else [],
                'timestamp': last_timestamp
            }
        else:
            if current_turn:
                current_turn['content'].append(line)
            elif line.strip(): # Lines at the beginning before any marker
                current_turn = {
                    'role': 'system',
                    'content': [line],
                    'timestamp': last_timestamp
                }

    if current_turn:
        turns.append(current_turn)

    # --- Post-processing and Writing to CSV ---
    turn_number = 1
    is_initial_block = True
    for turn in turns:
        content_str = "\n".join(turn['content']).strip()
        
        # Heuristic: If initial turns are `tool` roles about reading files, change them to `system`.
        if is_initial_block and turn['role'] == 'tool' and ('Referenced file' in content_str or 'Read ' in content_str):
            turn['role'] = 'system'
        # Stop this heuristic after the first non-system/setup-like turn
        elif turn['role'] not in ['system', 'tool'] or 'Conversation compacted' in content_str:
            is_initial_block = False

        if content_str: # Don't write empty turns
            writer.writerow([
                filename,
                turn_number,
                turn['role'],
                content_str,
                turn['timestamp'],
                source_file
            ])
            turn_number += 1
            
    # Every file MUST produce at least one turn. If none were found, dump content as a system message.
    if turn_number == 1 and content.strip():
        writer.writerow([
            filename,
            1,
            'system',
            f"[Parsing error: No turns detected. Full file content below.]\n\n{content.strip()}",
            last_timestamp,
            source_file
        ])

# --- Execution ---
try:
    parse_conversations(INPUT_FILE, OUTPUT_FILE)
    # The problem asks for the output to be named parsed_conversations.csv, so no print statement is needed.
except Exception as e:
    # Log errors if any occur during parsing
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        writer.writerow(CSV_HEADER)
        writer.writerow(["PARSING_FAILED", 1, "system", f"An unexpected error occurred: {e}", None, "N/A"])

```
