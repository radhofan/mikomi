import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import HTTPException
import instructor
import litellm

from api.schemas import SourceChannel, SourceExtraction

PROJ_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJ_ROOT / ".env")

EXTRACTION_SYSTEM_PROMPT = """You are an expert CRM lead management assistant.
Analyze the provided lead notes and extract the primary marketing or sales acquisition source.

Classify the source into exactly one of these allowed channels:
- Website: Form submissions, online demo requests, landing page visits.
- Event: In-person conferences, summits, trade shows, booths, QR code scans at events.
- LinkedIn: Messages, InMail, networking, or outreach on LinkedIn.
- Organic Search: Search engine discovery (e.g. Google, Bing, DuckDuckGo).
- Referral: Direct introductions or recommendations from clients, partners, or colleagues.
- Manual/Sales: Outbound cold calls, sales meetings, direct inbound calls to sales team, presentation follow-ups.
- Other: General conversations or ambiguous notes lacking sufficient channel evidence.

Rules:
- Never invent or assume information not grounded in the notes.
- If evidence is ambiguous or absent, use Other.
- Keep the detail concise and human-readable.

Examples:
- Notes: "Met him at the SFF booth, scanned our QR code"
  channel: Event
  detail: "Singapore FinTech Festival 2026 - Booth QR Code"

- Notes: "Found us through organic google search then booked a demo"
  channel: Organic Search
  detail: "Google organic search"

- Notes: "Sarah from Acme referred John to us"
  channel: Referral
  detail: "Referred by Sarah from Acme"

- Notes: "Connected with him on LinkedIn and discussed our product"
  channel: LinkedIn
  detail: "LinkedIn outreach"

- Notes: "Filled out the contact form on our website"
  channel: Website
  detail: "Website contact form"

- Notes: "Called the sales team directly after seeing our presentation"
  channel: Manual/Sales
  detail: "Direct sales contact"

- Notes: "Had a conversation with the prospect"
  channel: Other
  detail: "General prospect conversation"
"""


class AIService:
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.api_base = api_base or os.getenv("LLM_API_BASE")
        self.client = instructor.from_litellm(litellm.completion)

    def extract_source(self, notes: str) -> SourceExtraction:
        text = notes.strip() if notes else ""
        if not text:
            return SourceExtraction(
                channel=SourceChannel.OTHER,
                detail="Empty notes",
            )

        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Notes: {text}"},
            ],
            "response_model": SourceExtraction,
            "temperature": 0.0,
        }

        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base

        try:
            result: SourceExtraction = self.client.chat.completions.create(**kwargs)
            return result
        except litellm.exceptions.AuthenticationError as exc:
            raise HTTPException(
                status_code=401,
                detail=f"LLM authentication failed: {str(exc)}",
            )
        except Exception as exc:
            if "api_key" in str(exc).lower() or "authentication" in str(exc).lower():
                raise HTTPException(
                    status_code=401,
                    detail=f"LLM authentication error: {str(exc)}",
                )
            raise HTTPException(
                status_code=502,
                detail=f"LLM extraction error: {str(exc)}",
            )


_ai_service_instance: Optional[AIService] = None


def get_ai_service() -> AIService:
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance
