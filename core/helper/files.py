import json
import os
import re
import tempfile


def write_to_file(path, data):
    _ensure_parent(path)
    with open(path, "w", encoding="utf-8") as file:
        file.write(data)


def json_write_file(path, data):
    _ensure_parent(path)
    directory = os.path.dirname(path) or "."
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=directory, delete=False) as file:
        json.dump(data, file, indent=4)
        temp_name = file.name
    os.replace(temp_name, path)


def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return None
    except Exception as e:
        return None


def json_read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def sanitize_filename(filename, max_character_threshold: int = 40):
    # Define a regex pattern to match invalid characters
    filename = filename.replace("https://", "").replace("www.", "").replace("http://", "").replace(" ", "_")
    if len(filename) > max_character_threshold:
        filename = filename[:max_character_threshold]
    invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
    # Replace invalid characters with an underscore
    sanitized = re.sub(invalid_chars, '_', filename)
    # Remove leading or trailing spaces and periods
    sanitized = sanitized.strip(' .')
    return sanitized


def is_valid_url(url, base_url):
    # This regular expression matches URLs ending with .html or URLs without any extension
    text = url[len(base_url):]
    if "." in text:
        return text.endswith(".html")
    elif "#" in text:
        return False
    else:
        return True


def process_double_newlines(content):
    while '\n\n' in content:
        content = content.replace('\n\n', '\n')
    return content


def _ensure_parent(path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
