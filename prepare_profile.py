"""
STEP 1: Prepare profile once from a full skills/resume PDF
File: prepare_profile.py

This script parses your full skills/resume PDF and stores a structured profile locally.
"""

import argparse
import json
import PyPDF2
from typing import Any, Dict

from llm_client import LLMClient
from profile_memory import ProfileMemory
from pdf_text_extractor import extract_pdf_text_any


class ProfilePreparer:
    def __init__(self, backend: str = "ollama", model: str = "mistral", ollama_url: str = "http://localhost:11434", anthropic_key: str | None = None, profile_path: str = "profile_structure.json"):
        self.client = LLMClient.from_config(backend=backend, model=model, ollama_url=ollama_url, anthropic_key=anthropic_key)
        self.memory = ProfileMemory(path=profile_path)

    def extract_pdf_text(self, pdf_path: str, ocr_lang: str | None) -> str:
        """Extract text using layered strategies (PyPDF2, pdfminer, OCR)."""
        return extract_pdf_text_any(pdf_path, ocr_lang=ocr_lang)

    def _generate(self, prompt: str) -> str:
        return self.client.generate(prompt)

    def structure_profile(self, raw_text: str) -> Dict[str, Any]:
        """Use the configured LLM to structure the profile into a normalized English JSON."""
        prompt = f"""You are an HR expert. Analyze this full resume text and return ONLY a valid JSON with exactly this schema and English keys:

{{
  "identity": {{
    "name": "Full Name",
    "title": "Exact professional title"
  }},
  "long_profile": "Comprehensive profile description in 5-6 lines",
  "experiences": [
    {{
      "company": "Exact company name",
      "location": "Exact city",
      "role": "Exact job title",
      "dates": "YYYY-YYYY",
      "missions": ["detailed mission 1", "detailed mission 2", "detailed mission 3", "mission 4", "mission 5"]
    }}
  ],
  "skills": {{
    "technical": ["all technical skills"],
    "methodological": ["all methodological skills"]
  }},
  "education": "Main education with school, degree and dates",
  "languages": ["Language (level)", "Language (level)"],
  "interests": ["interest 1", "interest 2", "interest 3"]
}}

CRITICAL:
- Use REAL values from the resume (real company names, real cities, real dates)
- List ALL missions for each experience (up to 5 per experience)
- Return ONLY the JSON, with no extra text.

RESUME TEXT:
{raw_text}
"""
        print("🤖 Analyzing resume to structure profile...")
        response = self._generate(prompt)
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
            else:
                data = json.loads(response)
        except json.JSONDecodeError:
            print("❌ JSON parsing error from model output")
            print("Raw output:", response[:500])
            raise
        return data

    def prepare(self, pdf_path: str, ocr_lang: str | None = None) -> Dict[str, Any]:
        """Prepare and persist the structured profile."""
        print("📄 Extracting PDF text...")
        text = self.extract_pdf_text(pdf_path, ocr_lang)

        print("🧠 Structuring profile with LLM...")
        structured = self.structure_profile(text)

        # Persist using standardized file
        self.memory.save(structured)

        print("✅ Profile prepared and saved to 'profile_structure.json'")
        print(f"   → Name: {structured['identity']['name']}")
        print(f"   → {len(structured['experiences'])} experiences")
        print(f"   → {len(structured['skills']['technical'])} technical skills")
        return structured


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare structured profile from a PDF using Claude or local Ollama model.")
    parser.add_argument("pdf", help="Path to your full skills/resume PDF")
    parser.add_argument("--backend", choices=["ollama", "claude"], default="ollama", help="LLM backend to use")
    parser.add_argument("--model", default="mistral", help="Model name (e.g., mistral for Ollama or claude-3-5-sonnet-latest for Claude)")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--anthropic-key", default=None, help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    parser.add_argument("--profile-file", default="profile_structure.json", help="Where to store the structured profile")
    parser.add_argument("--ocr-lang", default=None, help="OCR language code for scanned PDFs (e.g., 'eng', 'fra')")

    args = parser.parse_args()

    preparer = ProfilePreparer(
        backend=args.backend,
        model=args.model,
        ollama_url=args.ollama_url,
        anthropic_key=args.anthropic_key,
        profile_path=args.profile_file,
    )
    preparer.prepare(args.pdf, ocr_lang=args.ocr_lang)


