import os
from fastapi import UploadFile
import pytesseract
from pdf2image import convert_from_bytes

async def process_patient_pdf(file: UploadFile):
    content = await file.read()

    # convert PDF → images
    pages = convert_from_bytes(content)

    # only page 1 for patient info
    page1 = pages[0]

    text = pytesseract.image_to_string(page1)

    # simple pattern extraction (we refine later)
    extracted = extract_patient_fields(text)

    return extracted


def extract_patient_fields(text: str):
    lines = text.splitlines()

    data = {
        "full_name": None,
        "id_number": None,
        "dob": None,
        "email": None,
        "address": None,
        "medical_aid": None,
        "file_number": None,
    }

    for line in lines:
        if "ID" in line or "Id" in line:
            data["id_number"] = "".join([c for c in line if c.isdigit()])
        if "@" in line:
            data["email"] = line.strip()
        # etc — we add more patterns later

    return data
