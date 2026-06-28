import os, uuid, random, string
from fastapi import UploadFile, HTTPException
from pathlib import Path

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "static/uploads")
MAX_MB     = int(os.getenv("MAX_FILE_SIZE_MB", 5))
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


async def save_upload(file: UploadFile, folder: str = "misc") -> str:
    """Save an uploaded file and return its relative path."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"File type {file.content_type} not allowed")

    contents = await file.read()
    if len(contents) > MAX_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large (max {MAX_MB} MB)")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"

    save_dir = Path(UPLOAD_DIR) / folder
    save_dir.mkdir(parents=True, exist_ok=True)

    save_path = save_dir / filename
    with open(save_path, "wb") as f:
        f.write(contents)

    return f"{UPLOAD_DIR}/{folder}/{filename}"


def generate_referral_code(length: int = 8) -> str:
    """Generate a unique-ish referral code."""
    chars = string.ascii_uppercase + string.digits
    return "NB" + "".join(random.choices(chars, k=length))
