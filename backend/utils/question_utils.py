import re

def normalize_options(options):
    # Normalize options to a consistent format (e.g., "A. Option 1")
    normalized_options = []
    for option in options:
        # Extract the letter (A, B, C, D) and append a period
        match = re.match(r"([A-Za-z])[).:-]?\s*(.*)", option)
        if match:
            letter, text = match.groups()
            normalized_options.append(f"{letter.upper()}. {text.strip()}")
    return normalized_options