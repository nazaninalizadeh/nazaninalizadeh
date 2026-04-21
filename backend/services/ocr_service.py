"""
OCR Service using OpenAI Vision via emergentintegrations.
Scans passport and ID images and extracts structured data.
"""

import os
import json
import re
import base64
import uuid
import logging
from datetime import datetime, timezone

from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from database import db

logger = logging.getLogger("ocr_service")

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")

OCR_SYSTEM_PROMPT = """You are a document OCR specialist. You analyze passport and identity document images and extract structured information.

CRITICAL: Return ONLY a raw JSON object. No markdown, no code fences, no explanation text before or after.

If a field is not visible or unreadable, use null.
Dates must be YYYY-MM-DD format.
Names in title case.
Gender: "M" or "F" or null.

JSON schema:
{"full_name":"string|null","passport_number":"string|null","nationality":"string|null","date_of_birth":"YYYY-MM-DD|null","gender":"M/F|null","place_of_birth":"string|null","issue_date":"YYYY-MM-DD|null","expiry_date":"YYYY-MM-DD|null","document_type":"passport|id_card|other","issuing_authority":"string|null","codice_fiscale":"string|null","confidence":"high|medium|low"}"""


def _extract_json(text: str) -> dict:
    """Extract JSON from response text, handling markdown code blocks and extra text."""
    text = text.strip()

    # Remove markdown code fences
    if "```" in text:
        match = re.search(r'```(?:json)?\s*\n?(.*?)```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError("No valid JSON found in response", text, 0)


async def scan_document(image_bytes: bytes, filename: str) -> dict:
    """
    Scan a passport/ID image using OpenAI Vision and extract structured data.
    Returns OCR result dict with extracted fields and metadata.
    """
    scan_id = str(uuid.uuid4())

    ocr_record = {
        "id": scan_id,
        "filename": filename,
        "status": "processing",
        "extracted_data": None,
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.ocr_scans.insert_one(ocr_record)

    try:
        if not EMERGENT_LLM_KEY:
            raise ValueError("EMERGENT_LLM_KEY not configured")

        # Convert image to base64
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Validate it looks like a real image
        if len(image_b64) < 100:
            raise ValueError("Image too small or invalid")

        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"ocr-{scan_id}",
            system_message=OCR_SYSTEM_PROMPT,
        )
        # Use gpt-4o-mini for cost efficiency - still has excellent vision capabilities
        chat.with_model("openai", "gpt-4o-mini")

        image_content = ImageContent(image_base64=image_b64)
        user_message = UserMessage(
            text="Extract all fields from this passport/ID document image. Return ONLY the JSON object, nothing else.",
            file_contents=[image_content],
        )

        response = await chat.send_message(user_message)
        logger.info(f"OCR raw response length: {len(response)}")

        extracted_data = _extract_json(response)

        await db.ocr_scans.update_one(
            {"id": scan_id},
            {"$set": {
                "status": "completed",
                "extracted_data": extracted_data,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }},
        )

        return {
            "id": scan_id,
            "status": "completed",
            "extracted_data": extracted_data,
        }

    except json.JSONDecodeError as e:
        logger.error(f"OCR JSON parse error: {e}")
        await db.ocr_scans.update_one(
            {"id": scan_id},
            {"$set": {"status": "failed", "error": f"Could not parse AI response"}},
        )
        return {"id": scan_id, "status": "failed", "error": "Impossibile elaborare la risposta. Riprova."}

    except Exception as e:
        error_str = str(e)
        logger.error(f"OCR scan error: {error_str}")

        # Provide user-friendly error messages
        if "Budget has been exceeded" in error_str or "budget" in error_str.lower():
            user_error = "Credito esaurito. Vai su Profile → Universal Key → Add Balance per ricaricare."
        elif "unsupported image" in error_str.lower():
            user_error = "Formato immagine non supportato. Usa una foto chiara in JPEG o PNG."
        elif "rate limit" in error_str.lower() or "429" in error_str:
            user_error = "Troppe richieste. Attendi qualche secondo e riprova."
        else:
            user_error = "Errore durante la scansione. Riprova con un'immagine piu chiara."

        await db.ocr_scans.update_one(
            {"id": scan_id},
            {"$set": {"status": "failed", "error": user_error}},
        )
        return {"id": scan_id, "status": "failed", "error": user_error}


async def get_scan_status(scan_id: str) -> dict:
    """Get the status and result of an OCR scan."""
    record = await db.ocr_scans.find_one({"id": scan_id}, {"_id": 0})
    if not record:
        return None
    return record
