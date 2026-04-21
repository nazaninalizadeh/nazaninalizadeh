"""
OCR Service using OpenAI Vision via emergentintegrations.
Scans passport and ID images and extracts structured data.
"""

import os
import json
import base64
import uuid
import logging
from datetime import datetime, timezone

from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from database import db

logger = logging.getLogger("ocr_service")

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")

OCR_SYSTEM_PROMPT = """You are a document OCR specialist. You analyze passport and identity document images and extract structured information.

IMPORTANT RULES:
- Return ONLY valid JSON, no markdown, no explanation, no extra text.
- If a field is not visible or unreadable, use null for that field.
- Dates should be in YYYY-MM-DD format when possible.
- Names should be in title case.
- Be precise with passport/ID numbers - include all characters exactly as shown.
- For gender, use "M" for male, "F" for female, or null if not visible.

Return a JSON object with these fields:
{
  "full_name": "string or null",
  "passport_number": "string or null",
  "nationality": "string or null",
  "date_of_birth": "YYYY-MM-DD or null",
  "gender": "M/F or null",
  "place_of_birth": "string or null",
  "issue_date": "YYYY-MM-DD or null",
  "expiry_date": "YYYY-MM-DD or null",
  "document_type": "passport/id_card/other",
  "issuing_authority": "string or null",
  "codice_fiscale": "string or null",
  "confidence": "high/medium/low"
}"""


async def scan_document(image_bytes: bytes, filename: str) -> dict:
    """
    Scan a passport/ID image using OpenAI Vision and extract structured data.
    Returns OCR result dict with extracted fields and metadata.
    """
    scan_id = str(uuid.uuid4())

    # Create OCR record with pending status
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

        # Create chat instance for this scan
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"ocr-{scan_id}",
            system_message=OCR_SYSTEM_PROMPT,
        )
        chat.with_model("openai", "gpt-4o")

        image_content = ImageContent(image_base64=image_b64)
        user_message = UserMessage(
            text="Analyze this passport or identity document image. Extract all visible information and return the structured JSON.",
            file_contents=[image_content],
        )

        response = await chat.send_message(user_message)

        # Parse the JSON response
        response_text = response.strip()
        # Remove markdown code block if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        extracted_data = json.loads(response_text)

        # Update record with success
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
            {"$set": {"status": "failed", "error": f"Could not parse AI response: {str(e)}"}},
        )
        return {"id": scan_id, "status": "failed", "error": "Could not parse document data"}

    except Exception as e:
        logger.error(f"OCR scan error: {e}")
        await db.ocr_scans.update_one(
            {"id": scan_id},
            {"$set": {"status": "failed", "error": str(e)}},
        )
        return {"id": scan_id, "status": "failed", "error": str(e)}


async def get_scan_status(scan_id: str) -> dict:
    """Get the status and result of an OCR scan."""
    record = await db.ocr_scans.find_one({"id": scan_id}, {"_id": 0})
    if not record:
        return None
    return record
