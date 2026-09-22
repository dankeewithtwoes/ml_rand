"""Wake-word detection that avoids substring activations and preserves commands."""
import re


def extract_command(text: str, wake_word: str) -> str | None:
    if not wake_word.strip(): raise ValueError("wake word cannot be empty")
    pattern = re.compile(rf"(?<!\w){re.escape(wake_word.strip())}(?!\w)", re.IGNORECASE)
    match = pattern.search(text)
    if not match: return None
    return (text[:match.start()] + " " + text[match.end():]).strip(" ,.!?:;-\t\n")
