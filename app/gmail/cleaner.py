import re
from bs4 import BeautifulSoup

REPLY_PATTERNS = [
    r"^On .* wrote:$",
    r"^From: .*",
    r"^Sent: .*",
    r"^To: .*",
    r"^Subject: .*",
]

SIGNATURE_PATTERNS = [
    r"^--\s*$",
    r"^__+$",
    r"^Sent from my .*",
    r"^Mit freundlichen Grüßen",
    r"^Best regards",
    r"^Kind regards",
]

MAX_CHARS = 4000


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")


def strip_quoted_replies(text: str) -> str:
    lines = text.splitlines()
    cleaned = []

    for line in lines:
        if any(re.match(p, line) for p in REPLY_PATTERNS):
            break
        cleaned.append(line)

    return "\n".join(cleaned)


def strip_signature(text: str) -> str:
    lines = text.splitlines()
    result = []

    for line in lines:
        if any(re.match(p, line) for p in SIGNATURE_PATTERNS):
            break
        result.append(line)

    return "\n".join(result)


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_email(text: str) -> str:
    if "<html" in text.lower():
        text = html_to_text(text)

    text = strip_quoted_replies(text)
    text = strip_signature(text)
    text = normalize_whitespace(text)

    return text[:MAX_CHARS]
