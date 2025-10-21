"""
STEP 2: Generate a tailored resume for each job offer
File: generate_resume.py

Run this script, paste the job offer, and get a personalized resume PDF.
"""

import argparse
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT
import re

from llm_client import LLMClient
from profile_memory import ProfileMemory


class ResumeGenerator:
    def __init__(self, backend: str = "ollama", model: str = "mistral", ollama_url: str = "http://localhost:11434", anthropic_key: str | None = None, profile_path: str = "profile_structure.json"):
        self.client = LLMClient.from_config(backend=backend, model=model, ollama_url=ollama_url, anthropic_key=anthropic_key)
        self.memory = ProfileMemory(path=profile_path)
        self.profile = self._load_profile()

    def _load_profile(self):
        try:
            profile = self.memory.load()
            print(f"✅ Profile loaded: {profile['identity']['name']}")
            return profile
        except FileNotFoundError as e:
            print(str(e))
            print("Run 'prepare_profile.py' first to create your profile.")
            exit(1)

    def _generate(self, prompt: str) -> str:
        return self.client.generate(prompt)

    def extract_job_title(self, offer: str):
        """Extract job title from the offer text."""
        prompt = f"""Extract the job title from this offer. Return ONLY the title, nothing else.

Offer:
{offer[:1000]}

Job title:"""

        response = self._generate(prompt)
        title = response.strip().replace('\n', ' ')

        title = re.sub(r'[<>:"/\\|?*]', '', title)
        title = title[:50]

        return title if title else None

    def adapt_profile(self, offer: str):
        """Adapt the profile summary to the offer."""
        prompt = f"""You are a resume writing expert.

JOB OFFER:
{offer}

FULL CANDIDATE PROFILE:
{self.profile['long_profile']}

Write a 4-5 line profile paragraph highlighting the most relevant points for this offer.
Use keywords from the offer. Be specific and impactful.
Return ONLY the paragraph without any preface or comments."""

        return self._generate(prompt)

    def select_experiences(self, offer: str):
        """Select and adapt the most relevant experiences."""
        experiences_json = json.dumps(self.profile['experiences'], ensure_ascii=False, indent=2)

        prompt = f"""You are a resume writing expert.

JOB OFFER:
{offer}

CANDIDATE EXPERIENCES (JSON):
{experiences_json}

Select the 2-3 MOST relevant experiences and adapt missions to match the offer.
For each experience, keep 4-5 detailed missions showcasing requested competencies.

IMPORTANT: Use REAL values from the JSON (real company names, cities, dates).

Return ONLY a valid JSON array of objects with this schema:
[
  {{
    "company": "Exact company name",
    "location": "Exact city",
    "role": "Exact role title",
    "dates": "Real dates",
    "missions": ["detailed mission 1", "detailed mission 2", "detailed mission 3", "detailed mission 4"]
  }}
]
"""

        response = self._generate(prompt)

        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return json.loads(response)
        except json.JSONDecodeError:
            print("⚠️ JSON parsing error for experiences, using first 2 experiences as fallback")
            return self.profile['experiences'][:2]

    def select_skills(self, offer: str):
        """Select relevant skills grouped by category, formatted in HTML spans for PDF."""
        skills_json = json.dumps(self.profile['skills'], ensure_ascii=False, indent=2)

        prompt = f"""You are a resume writing expert.

JOB OFFER:
{offer}

CANDIDATE SKILLS:
{skills_json}

Select the relevant skills for this offer (8-10 per category). Prioritize skills mentioned in the offer.
Return ONLY this exact HTML-like format:
<b>Technical:</b> skill1, skill2, skill3, skill4, skill5, skill6, skill7, skill8<br/>
<b>Management & Methods:</b> skill1, skill2, skill3, skill4, skill5, skill6
"""

        return self._generate(prompt)

    def generate_filename(self, job_title):
        """Generate the PDF filename."""
        if job_title:
            name = f"Resume_{job_title}"
        else:
            candidate_name = self.profile['identity']['name'].replace(' ', '_')
            date = datetime.now().strftime("%Y%m%d")
            name = f"Resume_{candidate_name}_{date}"

        name = re.sub(r'[<>:"/\\|?*]', '', name)
        return f"{name}.pdf"

    def generate_pdf(self, adapted_profile, experiences, skills, filename):
        """Generate the final PDF."""
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )

        styles = getSampleStyleSheet()

        style_title = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=4,
            textColor='#1a1a1a',
            fontName='Helvetica-Bold'
        )

        style_subtitle = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=11,
            spaceAfter=10,
            textColor='#444444'
        )

        style_section = ParagraphStyle(
            'CustomSection',
            parent=styles['Heading3'],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6,
            textColor='#2c3e50',
            fontName='Helvetica-Bold'
        )

        style_normal = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            leading=13,
            alignment=TA_LEFT,
            spaceAfter=3
        )

        style_experience = ParagraphStyle(
            'CustomExperience',
            parent=styles['Normal'],
            fontSize=10,
            leading=13,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=4
        )

        content = []

        # Header
        content.append(Paragraph(self.profile['identity']['name'], style_title))
        content.append(Paragraph(self.profile['identity']['title'], style_subtitle))
        content.append(Spacer(1, 8))

        # Profile
        content.append(Paragraph("<b>Profile</b>", style_section))
        content.append(Paragraph(adapted_profile, style_normal))
        content.append(Spacer(1, 10))

        # Experiences
        content.append(Paragraph("<b>Professional Experience</b>", style_section))
        for exp in experiences:
            exp_title = f"<b>{exp['company']} – {exp['location']}</b> | {exp['role']} ({exp['dates']})"
            content.append(Paragraph(exp_title, style_experience))

            missions_text = "<br/>".join([f"• {m}" for m in exp['missions']])
            content.append(Paragraph(missions_text, style_normal))
            content.append(Spacer(1, 8))

        # Skills
        content.append(Paragraph("<b>Skills</b>", style_section))
        content.append(Paragraph(skills, style_normal))
        content.append(Spacer(1, 10))

        # Education
        content.append(Paragraph("<b>Education</b>", style_section))
        content.append(Paragraph(self.profile['education'], style_normal))
        content.append(Spacer(1, 10))

        # Languages
        content.append(Paragraph("<b>Languages</b>", style_section))
        languages_text = " • ".join(self.profile['languages'])
        content.append(Paragraph(languages_text, style_normal))

        # Interests
        if 'interests' in self.profile and self.profile['interests']:
            content.append(Spacer(1, 10))
            content.append(Paragraph("<b>Interests</b>", style_section))
            if isinstance(self.profile['interests'], list):
                interests_text = ", ".join(self.profile['interests'])
            else:
                interests_text = self.profile['interests']
            content.append(Paragraph(interests_text, style_normal))

        # Build
        doc.build(content)
        print(f"✅ Resume generated: {filename}")

    def generate(self, job_offer: str):
        """End-to-end generation pipeline."""
        print("\n🎯 Analyzing the job offer...")

        # Extract title for filename
        print("📝 Extracting job title...")
        job_title = self.extract_job_title(job_offer)
        if job_title:
            print(f"   → Detected: {job_title}")

        # Adapt sections
        print("🤖 Adapting profile summary...")
        adapted_profile = self.adapt_profile(job_offer)

        print("🤖 Selecting experiences...")
        experiences = self.select_experiences(job_offer)

        print("🤖 Selecting skills...")
        skills = self.select_skills(job_offer)

        # Write memory note for future personalization
        if job_title:
            self.memory.record_adaptation_note(job_title, f"Generated resume tailored for: {job_title}")

        # Generate filename
        filename = self.generate_filename(job_title)

        # Generate the PDF
        print("📄 Generating PDF...")
        self.generate_pdf(adapted_profile, experiences, skills, filename)

        print(f"\n✨ DONE! Resume saved to: {filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a tailored resume from a job offer using Claude or local Ollama model.")
    parser.add_argument("--backend", choices=["ollama", "claude"], default="ollama", help="LLM backend to use")
    parser.add_argument("--model", default="mistral", help="Model name (e.g., mistral for Ollama or claude-3-5-sonnet-latest for Claude)")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--anthropic-key", default=None, help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    parser.add_argument("--profile-file", default="profile_structure.json", help="Path to structured profile file")

    args = parser.parse_args()

    print("=" * 60)
    print("   AUTOMATIC RESUME GENERATOR")
    print("=" * 60)
    print()

    generator = ResumeGenerator(
        backend=args.backend,
        model=args.model,
        ollama_url=args.ollama_url,
        anthropic_key=args.anthropic_key,
        profile_path=args.profile_file,
    )

    print("📋 Paste the job offer below, then press Enter twice:")
    print("-" * 60)

    lines = []
    while True:
        line = input()
        if line == "" and len(lines) > 0 and lines[-1] == "":
            break
        lines.append(line)

    job_offer = "\n".join(lines).strip()

    if not job_offer:
        print("❌ No job offer provided. Abort.")
        exit(1)

    generator.generate(job_offer)


