import re
import pytesseract
from pdf2image import convert_from_path

# YOUR TESSERACT PATH
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Brett-LT\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"


# FIX OCR MISREAD CHARACTERS → DIGITS
OCR_FIX = {
    'S': '5', 's': '5',
    'b': '6', 'B': '8',
    'I': '1', 'l': '1', 'i': '1',
    'O': '0', 'o': '0', 'D': '0',
    'Z': '2', 'z': '2', 'L': '2',
    'M': '1', 'N': '1',
    'G': '6', 'g': '9',
    'Q': '0',
    '|': '',
}


def ocr_first_page(file_path: str) -> str:
    pages = convert_from_path(file_path, dpi=300)
    if not pages:
        return ""
    return pytesseract.image_to_string(pages[0], lang="eng+afr")


def clean_digits(s: str) -> str:
    return "".join(re.findall(r"\d", s))


def extract_id(text: str) -> str | None:
    """Extract SA ID by fixing OCR noise THEN extracting digits."""
    m = re.search(r"ID\s*nr\s*[:\-]*\s*([A-Za-z0-9\s]+)", text, re.IGNORECASE)
    if not m:
        return None

    line = m.group(1)

    # Apply OCR_FIX to every character
    cleaned = "".join(OCR_FIX.get(c, c) for c in line)

    digits = clean_digits(cleaned)

    # Look for 13-digit ID
    m2 = re.search(r"\b\d{13}\b", digits)
    if m2:
        return m2.group(0)

    return None


def extract_phone(text: str) -> str | None:
    """Extract SA phone numbers even when OCR destroys prefixes."""

    # Find any digit group
    m = re.findall(r"\b[\d\s]{6,}\b", text)
    if not m:
        return None

    digits = clean_digits(m[0])

    # If phone too short (< 8 digits) → unusable
    if len(digits) < 8:
        return None

    # If 7 digits → assume 06 prefix (most common pattern in these forms)
    if len(digits) == 7:
        digits = "06" + digits

    # Ensure starts with 0
    if not digits.startswith("0"):
        digits = "0" + digits

    # Return first 10 digits
    return digits[:10]


def extract_all_emails(text: str) -> list:
    return re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)


def clean_email(email: str) -> str:
    email = email.lower()
    replacements = {
        "co.1d": "co.za",
        "co.ld": "co.za",
        "gmol.com": "gmail.com",
        "gmait.com": "gmail.com",
        "|": "",
    }
    for bad, good in replacements.items():
        email = email.replace(bad, good)
    return email


def choose_best_email(emails: list) -> str | None:
    """Choose the most 'legit' email."""
    if not emails:
        return None

    def score(e):
        name = e.split("@")[0]
        s = 0
        if any(c.isalpha() for c in name):
            s += 2
        if name.isalpha():
            s += 2
        if "gmail.com" in e:
            s += 1
        if "co.za" in e:
            s += 1
        return s

    cleaned = [clean_email(e) for e in emails]
    best = sorted(cleaned, key=score, reverse=True)[0]
    return best


def extract_names(text: str) -> dict:
    pref = None
    surname = None

    # Preferred name
    m = re.search(r"Noemnaam\s*[:\-]*\s*([A-Za-z]+)", text, re.IGNORECASE)
    if m:
        pref = m.group(1).title()

    # Surname
    m = re.search(r"Van\s*[:\-]*\s*([A-Za-z]+)", text, re.IGNORECASE)
    if m:
        surname = m.group(1).title()

    # Option A: preferred first
    if pref and surname:
        return {
            "full_name": f"{pref} {surname}".title(),
            "preferred_name": pref,
        }

    if pref:
        return {"full_name": pref, "preferred_name": pref}

    return {"full_name": None, "preferred_name": None}


def parse_patient_data(text: str) -> dict:
    names = extract_names(text)
    id_number = extract_id(text)
    phone = extract_phone(text)
    emails = extract_all_emails(text)

    email = choose_best_email(emails)

    return {
        "full_name": names.get("full_name"),
        "preferred_name": names.get("preferred_name"),
        "id_number": id_number,
        "email": email,
        "phone": phone,
    }
