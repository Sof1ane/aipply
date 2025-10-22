#!/usr/bin/env python3
"""
AI Resume Generator - Main Application
A comprehensive tool for generating tailored resumes using various AI models.
"""

import argparse
import json
import os
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from llm_client import LLMClient
from pdf_text_extractor import extract_pdf_text_any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML


class AIResumeGenerator:
    def __init__(self):
        self.client: Optional[LLMClient] = None
        self.profile: Dict[str, Any] = {}
        self.profile_file = "user_profile.json"
        
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_header(self, title: str):
        """Print a formatted header."""
        print("\n" + "=" * 80)
        print(f"   {title}")
        print("=" * 80)
        
    def get_user_choice(self, prompt: str, choices: List[str]) -> str:
        """Get user choice from a list of options."""
        while True:
            print(f"\n{prompt}")
            for i, choice in enumerate(choices, 1):
                print(f"  {i}. {choice}")
            
            try:
                choice_num = int(input("\nEnter your choice (number): "))
                if 1 <= choice_num <= len(choices):
                    return choices[choice_num - 1]
                else:
                    print("❌ Invalid choice. Please try again.")
            except ValueError:
                print("❌ Please enter a valid number.")
                
    def setup_llm_client(self) -> bool:
        """Setup the LLM client based on user's model choice."""
        self.print_header("AI MODEL SELECTION")
        
        models = [
            "OpenAI ChatGPT (GPT-4)",
            "Anthropic Claude",
            "Google Gemini",
            "Ollama (Local)"
        ]
        
        selected_model = self.get_user_choice("Choose your AI model:", models)
        
        if "ChatGPT" in selected_model:
            return self._setup_openai()
        elif "Claude" in selected_model:
            return self._setup_anthropic()
        elif "Gemini" in selected_model:
            return self._setup_gemini()
        elif "Ollama" in selected_model:
            return self._setup_ollama()
        else:
            print("❌ Invalid model selection.")
            return False
            
    def _setup_openai(self) -> bool:
        """Setup OpenAI client."""
        api_key = input("\nEnter your OpenAI API key: ").strip()
        if not api_key:
            print("❌ API key is required.")
            return False
            
        # Set environment variable for the session
        os.environ['OPENAI_API_KEY'] = api_key
        
        try:
            # For now, we'll use a mock client since we don't have OpenAI implementation
            print("⚠️ OpenAI integration not yet implemented. Please choose another model.")
            return False
        except Exception as e:
            print(f"❌ Error setting up OpenAI: {e}")
            return False
            
    def _setup_anthropic(self) -> bool:
        """Setup Anthropic client."""
        api_key = input("\nEnter your Anthropic API key: ").strip()
        if not api_key:
            print("❌ API key is required.")
            return False
            
        try:
            self.client = LLMClient.from_config(
                backend="claude",
                model="claude-3-5-sonnet-latest",
                anthropic_key=api_key
            )
            print("✅ Anthropic Claude client configured successfully!")
            return True
        except Exception as e:
            print(f"❌ Error setting up Anthropic: {e}")
            return False
            
    def _setup_gemini(self) -> bool:
        """Setup Google Gemini client."""
        api_key = input("\nEnter your Google Gemini API key: ").strip()
        if not api_key:
            print("❌ API key is required.")
            return False
            
        try:
            # For now, we'll use a mock client since we don't have Gemini implementation
            print("⚠️ Gemini integration not yet implemented. Please choose another model.")
            return False
        except Exception as e:
            print(f"❌ Error setting up Gemini: {e}")
            return False
            
    def _setup_ollama(self) -> bool:
        """Setup Ollama client with model selection and management."""
        print("\n🔍 Checking Ollama status...")
        
        # Check if Ollama is running
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ Ollama is running!")
                available_models = self._get_available_ollama_models()
            else:
                print("⚠️ Ollama is not running. Starting Ollama service...")
                if not self._start_ollama():
                    return False
                available_models = self._get_available_ollama_models()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Ollama is not installed or not accessible.")
            print("Please install Ollama from https://ollama.ai/")
            return False
            
        if not available_models:
            print("❌ No models found in Ollama.")
            return False
            
        # Let user choose or add a model
        print(f"\nAvailable models: {', '.join(available_models)}")
        choice = self.get_user_choice(
            "Choose an option:",
            ["Use existing model", "Pull a new model"]
        )
        
        if choice == "Use existing model":
            model_name = self.get_user_choice("Select a model:", available_models)
        else:
            model_name = self._pull_ollama_model()
            if not model_name:
                return False
                
        try:
            self.client = LLMClient.from_config(
                backend="ollama",
                model=model_name,
                ollama_url="http://localhost:11434"
            )
            print(f"✅ Ollama client configured with model: {model_name}")
            return True
        except Exception as e:
            print(f"❌ Error setting up Ollama: {e}")
            return False
            
    def _get_available_ollama_models(self) -> List[str]:
        """Get list of available Ollama models."""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                models = []
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
                return models
        except Exception as e:
            print(f"⚠️ Error getting Ollama models: {e}")
        return []
        
    def _pull_ollama_model(self) -> Optional[str]:
        """Pull a new Ollama model."""
        popular_models = [
            "llama3.2:3b",
            "llama3.2:1b", 
            "mistral:7b",
            "codellama:7b",
            "phi3:mini"
        ]
        
        model_name = self.get_user_choice("Choose a model to pull:", popular_models)
        
        print(f"\n🔄 Pulling {model_name}... This may take a few minutes.")
        try:
            result = subprocess.run(['ollama', 'pull', model_name], 
                                  capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                print(f"✅ Successfully pulled {model_name}")
                return model_name
            else:
                print(f"❌ Error pulling model: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            print("❌ Timeout while pulling model.")
            return None
        except Exception as e:
            print(f"❌ Error pulling model: {e}")
            return None
            
    def _start_ollama(self) -> bool:
        """Start Ollama service."""
        try:
            print("🔄 Starting Ollama service...")
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Wait a bit for service to start
            import time
            time.sleep(3)
            
            # Test if it's running
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error starting Ollama: {e}")
            return False
            
    def create_or_load_profile(self):
        """Create a new profile or load existing one."""
        self.print_header("PROFILE SETUP")
        
        if os.path.exists(self.profile_file):
            choice = self.get_user_choice(
                "Profile found. What would you like to do?",
                ["Use existing profile", "Create new profile from PDF", "Create new profile manually"]
            )
        else:
            choice = self.get_user_choice(
                "How would you like to create your profile?",
                ["Upload PDF resume", "Create manually"]
            )
            
        if choice == "Use existing profile":
            self._load_existing_profile()
        elif "PDF" in choice:
            self._create_profile_from_pdf()
        else:
            self._create_profile_manually()
            
    def _load_existing_profile(self):
        """Load existing profile."""
        try:
            with open(self.profile_file, 'r', encoding='utf-8') as f:
                self.profile = json.load(f)
            print(f"✅ Profile loaded: {self.profile['identity']['name']}")
        except Exception as e:
            print(f"❌ Error loading profile: {e}")
            self._create_profile_manually()
            
    def _create_profile_from_pdf(self):
        """Create profile from PDF resume."""
        pdf_path = input("\nEnter the path to your PDF resume: ").strip()
        
        if not os.path.exists(pdf_path):
            print("❌ PDF file not found.")
            self._create_profile_manually()
            return
            
        print("📄 Extracting text from PDF...")
        try:
            text = extract_pdf_text_any(pdf_path)
            if not text.strip():
                print("❌ Could not extract text from PDF.")
                self._create_profile_manually()
                return
                
            print("🤖 Analyzing resume with AI...")
            
            # Test API connection first
            try:
                test_response = self.client.generate("Hello, respond with 'OK' if you can process this request.")
                if "OK" not in test_response:
                    print("⚠️ API test failed. Using fallback profile creation.")
                    self.profile = self._create_basic_profile_from_text(text)
                else:
                    self.profile = self._structure_profile_with_ai(text)
            except Exception as api_error:
                print(f"⚠️ API connection issue: {api_error}")
                print("Using fallback profile creation...")
                self.profile = self._create_basic_profile_from_text(text)
                
            self._save_profile()
            print("✅ Profile created from PDF!")
            
            # Ask user to review and add missing information
            self._review_and_complete_profile()
            
        except Exception as e:
            print(f"❌ Error processing PDF: {e}")
            choice = self.get_user_choice(
                "PDF processing failed. What would you like to do?",
                ["Try manual profile creation", "Exit"]
            )
            if choice == "Try manual profile creation":
                self._create_profile_manually()
            else:
                print("👋 Goodbye!")
                sys.exit(0)
            
    def _create_profile_manually(self):
        """Create profile manually through user input."""
        print("\n📝 Let's create your profile step by step:")
        
        # Basic information
        name = input("\nEnter your full name: ").strip()
        email = input("Enter your email: ").strip()
        phone = input("Enter your phone number: ").strip()
        title = input("Enter your professional title: ").strip()
        location = input("Enter your location (city, country): ").strip()
        
        # Experiences
        print("\n💼 Now let's add your work experiences:")
        experiences = []
        while True:
            print(f"\nExperience #{len(experiences) + 1}:")
            company = input("Company name: ").strip()
            if not company:
                break
                
            role = input("Job title: ").strip()
            dates = input("Employment dates (e.g., 2020-2023): ").strip()
            location_exp = input("Location: ").strip()
            
            print("Enter your key responsibilities (one per line, empty line to finish):")
            missions = []
            while True:
                mission = input("• ").strip()
                if not mission:
                    break
                missions.append(mission)
                
            experiences.append({
                "company": company,
                "role": role,
                "dates": dates,
                "location": location_exp,
                "missions": missions
            })
            
            if not self.get_user_choice("Add another experience?", ["Yes", "No"]) == "Yes":
                break
                
        # Education
        print("\n🎓 Now let's add your education:")
        education = []
        while True:
            print(f"\nEducation #{len(education) + 1}:")
            degree = input("Degree/Qualification: ").strip()
            if not degree:
                break
                
            school = input("School/University: ").strip()
            dates = input("Dates (e.g., 2016-2020): ").strip()
            
            education.append({
                "degree": degree,
                "school": school,
                "dates": dates
            })
            
            if not self.get_user_choice("Add another education entry?", ["Yes", "No"]) == "Yes":
                break
                
        # Skills
        print("\n🛠️ Now let's add your skills:")
        technical_skills = input("Technical skills (comma-separated): ").strip().split(',')
        technical_skills = [skill.strip() for skill in technical_skills if skill.strip()]
        
        soft_skills = input("Soft skills (comma-separated): ").strip().split(',')
        soft_skills = [skill.strip() for skill in soft_skills if skill.strip()]
        
        # Languages
        languages = input("Languages (e.g., English (Native), French (Fluent)): ").strip()
        languages_list = [lang.strip() for lang in languages.split(',') if lang.strip()]
        
        # Create profile structure
        self.profile = {
            "identity": {
                "name": name,
                "title": title,
                "email": email,
                "phone": phone,
                "location": location
            },
            "experiences": experiences,
            "education": education,
            "skills": {
                "technical": technical_skills,
                "soft": soft_skills
            },
            "languages": languages_list,
            "long_profile": self._generate_profile_summary(name, title, experiences, technical_skills)
        }
        
        self._save_profile()
        print("✅ Profile created successfully!")
        
    def _generate_profile_summary(self, name: str, title: str, experiences: List[Dict], skills: List[str]) -> str:
        """Generate a professional summary using AI."""
        if not self.client:
            return f"Experienced {title} with expertise in {', '.join(skills[:3])}."
            
        experiences_text = "\n".join([
            f"- {exp['role']} at {exp['company']} ({exp['dates']})"
            for exp in experiences[:3]
        ])
        
        prompt = f"""Create a professional 3-4 line summary for this candidate:

Name: {name}
Title: {title}
Recent Experience:
{experiences_text}
Key Skills: {', '.join(skills[:5])}

Write a compelling professional summary that highlights their expertise and experience."""
        
        try:
            return self.client.generate(prompt)
        except Exception as e:
            print(f"⚠️ Could not generate AI summary: {e}")
            return f"Experienced {title} with expertise in {', '.join(skills[:3])}."
            
    def _structure_profile_with_ai(self, text: str) -> Dict[str, Any]:
        """Structure profile from text using AI."""
        # Truncate text to avoid token limits
        truncated_text = text[:2000]  # Reduced from 3000 to 2000
        
        prompt = f"""Analyze this resume and return ONLY valid JSON with this exact structure:

{{
  "identity": {{
    "name": "Full Name",
    "title": "Professional Title",
    "email": "email@example.com",
    "phone": "phone number",
    "location": "city, country"
  }},
  "long_profile": "4-5 line professional summary",
  "experiences": [
    {{
      "company": "Company Name",
      "location": "City",
      "role": "Job Title",
      "dates": "YYYY-YYYY",
      "missions": ["mission 1", "mission 2", "mission 3"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree",
      "school": "School",
      "dates": "YYYY-YYYY"
    }}
  ],
  "skills": {{
    "technical": ["skill1", "skill2"],
    "soft": ["skill1", "skill2"]
  }},
  "languages": ["Language (level)"]
}}

RESUME:
{truncated_text}

Return ONLY the JSON:"""
        
        try:
            response = self.client.generate(prompt)
            
            # Try to extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                profile_data = json.loads(json_str)
                
                # Validate that we have the required fields
                if 'identity' in profile_data and 'name' in profile_data['identity']:
                    return profile_data
                else:
                    print("⚠️ AI response missing required fields. Using fallback.")
                    return self._create_basic_profile_from_text(text)
            else:
                print("⚠️ Could not find JSON in AI response. Using fallback.")
                return self._create_basic_profile_from_text(text)
                
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parsing error: {e}. Using fallback.")
            return self._create_basic_profile_from_text(text)
        except Exception as e:
            print(f"⚠️ AI processing error: {e}. Using fallback.")
            return self._create_basic_profile_from_text(text)
            
    def _create_basic_profile_from_text(self, text: str) -> Dict[str, Any]:
        """Create a basic profile structure from text when AI parsing fails."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Extract basic information using simple text parsing
        name = "Unknown"
        email = ""
        phone = ""
        title = "Professional"
        location = ""
        
        # Look for email and phone patterns
        import re
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            email = email_match.group()
            
        phone_match = re.search(r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})', text)
        if phone_match:
            phone = phone_match.group()
        
        # Try to extract name from the beginning of the text
        # Look for a line that looks like a name (starts with capital, not too long, no special chars)
        for line in lines[:10]:
            if (len(line) < 50 and 
                line[0].isupper() and 
                not any(char in line for char in ['@', '•', ':', '(', ')', '—']) and
                not any(word in line.lower() for word in ['engineer', 'developer', 'manager', 'analyst', 'consultant', 'specialist', 'profil', 'langues', 'secteurs'])):
                name = line
                break
        
        # Try to find a title
        for line in lines[:10]:
            if any(word in line.lower() for word in ['engineer', 'developer', 'manager', 'analyst', 'consultant', 'specialist']):
                title = line
                break
        
        # Extract skills from the text
        technical_skills = []
        soft_skills = []
        
        # Look for common technical skills
        tech_keywords = ['python', 'sql', 'java', 'javascript', 'react', 'node', 'aws', 'azure', 'docker', 'kubernetes', 'git', 'linux', 'data', 'analytics', 'bi', 'ai', 'ml']
        for keyword in tech_keywords:
            if keyword.lower() in text.lower():
                technical_skills.append(keyword.title())
        
        # Look for soft skills
        soft_keywords = ['communication', 'leadership', 'teamwork', 'problem solving', 'analytical', 'creative', 'adaptable']
        for keyword in soft_keywords:
            if keyword.lower() in text.lower():
                soft_skills.append(keyword.title())
        
        return {
            "identity": {
                "name": name,
                "title": title,
                "email": email,
                "phone": phone,
                "location": location
            },
            "long_profile": f"Experienced {title} with diverse professional background.",
            "experiences": [],
            "education": [],
            "skills": {
                "technical": technical_skills,
                "soft": soft_skills
            },
            "languages": []
        }
        
    def _review_and_complete_profile(self):
        """Review the extracted profile and ask user to complete missing information."""
        self.print_header("PROFILE REVIEW & COMPLETION")
        
        print("📋 Here's what we extracted from your PDF:")
        print(f"   Name: {self.profile['identity']['name']}")
        print(f"   Title: {self.profile['identity']['title']}")
        print(f"   Email: {self.profile['identity']['email'] or 'Not found'}")
        print(f"   Phone: {self.profile['identity']['phone'] or 'Not found'}")
        print(f"   Location: {self.profile['identity']['location'] or 'Not found'}")
        print(f"   Experiences: {len(self.profile['experiences'])} found")
        print(f"   Education: {len(self.profile['education'])} found")
        print(f"   Technical Skills: {len(self.profile['skills']['technical'])} found")
        print(f"   Languages: {len(self.profile['languages'])} found")
        
        print("\n❓ Would you like to add or correct any missing information?")
        choice = self.get_user_choice("Choose an option:", ["Yes, let me add missing info", "No, the profile is complete"])
        
        if choice == "Yes, let me add missing info":
            self._complete_missing_info()
            
    def _complete_missing_info(self):
        """Allow user to complete missing profile information."""
        print("\n📝 Let's complete your profile. Press Enter to skip any field you don't want to change.")
        
        # Basic information
        current_name = self.profile['identity']['name']
        new_name = input(f"Name (current: {current_name}): ").strip()
        if new_name:
            self.profile['identity']['name'] = new_name
            
        current_title = self.profile['identity']['title']
        new_title = input(f"Professional title (current: {current_title}): ").strip()
        if new_title:
            self.profile['identity']['title'] = new_title
            
        current_email = self.profile['identity']['email']
        new_email = input(f"Email (current: {current_email or 'None'}): ").strip()
        if new_email:
            self.profile['identity']['email'] = new_email
            
        current_phone = self.profile['identity']['phone']
        new_phone = input(f"Phone (current: {current_phone or 'None'}): ").strip()
        if new_phone:
            self.profile['identity']['phone'] = new_phone
            
        current_location = self.profile['identity']['location']
        new_location = input(f"Location (current: {current_location or 'None'}): ").strip()
        if new_location:
            self.profile['identity']['location'] = new_location
        
        # Add experiences if none found
        if not self.profile['experiences']:
            print("\n💼 No work experiences found. Would you like to add some?")
            if self.get_user_choice("Add work experiences?", ["Yes", "No"]) == "Yes":
                self._add_experiences()
        
        # Add education if none found
        if not self.profile['education']:
            print("\n🎓 No education found. Would you like to add some?")
            if self.get_user_choice("Add education?", ["Yes", "No"]) == "Yes":
                self._add_education()
        
        # Add skills if few found
        if len(self.profile['skills']['technical']) < 3:
            print("\n🛠️ Few technical skills found. Would you like to add more?")
            if self.get_user_choice("Add more skills?", ["Yes", "No"]) == "Yes":
                self._add_skills()
        
        # Add languages if none found
        if not self.profile['languages']:
            print("\n🌍 No languages found. Would you like to add some?")
            if self.get_user_choice("Add languages?", ["Yes", "No"]) == "Yes":
                self._add_languages()
        
        self._save_profile()
        print("✅ Profile updated successfully!")
        
    def _add_experiences(self):
        """Add work experiences to the profile."""
        while True:
            print(f"\nExperience #{len(self.profile['experiences']) + 1}:")
            company = input("Company name: ").strip()
            if not company:
                break
                
            role = input("Job title: ").strip()
            dates = input("Employment dates (e.g., 2020-2023): ").strip()
            location = input("Location: ").strip()
            
            print("Enter your key responsibilities (one per line, empty line to finish):")
            missions = []
            while True:
                mission = input("• ").strip()
                if not mission:
                    break
                missions.append(mission)
                
            self.profile['experiences'].append({
                "company": company,
                "role": role,
                "dates": dates,
                "location": location,
                "missions": missions
            })
            
            if not self.get_user_choice("Add another experience?", ["Yes", "No"]) == "Yes":
                break
                
    def _add_education(self):
        """Add education to the profile."""
        while True:
            print(f"\nEducation #{len(self.profile['education']) + 1}:")
            degree = input("Degree/Qualification: ").strip()
            if not degree:
                break
                
            school = input("School/University: ").strip()
            dates = input("Dates (e.g., 2016-2020): ").strip()
            
            self.profile['education'].append({
                "degree": degree,
                "school": school,
                "dates": dates
            })
            
            if not self.get_user_choice("Add another education entry?", ["Yes", "No"]) == "Yes":
                break
                
    def _add_skills(self):
        """Add skills to the profile."""
        print("\nTechnical skills (comma-separated):")
        tech_skills = input("").strip().split(',')
        tech_skills = [skill.strip() for skill in tech_skills if skill.strip()]
        self.profile['skills']['technical'].extend(tech_skills)
        
        print("\nSoft skills (comma-separated):")
        soft_skills = input("").strip().split(',')
        soft_skills = [skill.strip() for skill in soft_skills if skill.strip()]
        self.profile['skills']['soft'].extend(soft_skills)
        
    def _add_languages(self):
        """Add languages to the profile."""
        languages = input("Languages (e.g., English (Native), French (Fluent)): ").strip()
        languages_list = [lang.strip() for lang in languages.split(',') if lang.strip()]
        self.profile['languages'].extend(languages_list)
        
    def _save_profile(self):
        """Save profile to file."""
        with open(self.profile_file, 'w', encoding='utf-8') as f:
            json.dump(self.profile, f, indent=2, ensure_ascii=False)
            
    def generate_resume_workflow(self):
        """Main resume generation workflow."""
        while True:
            self.print_header("RESUME GENERATION")
            
            print("📋 Paste the job description below, then press Enter twice:")
            print("-" * 80)
            
            lines = []
            while True:
                line = input()
                if line == "" and len(lines) > 0 and lines[-1] == "":
                    break
                lines.append(line)
                
            job_description = "\n".join(lines).strip()
            
            if not job_description:
                print("❌ No job description provided.")
                continue
                
            print("\n🤖 Generating tailored resume...")
            
            try:
                # Let user choose style
                style_choice = self.get_user_choice(
                    "Choose a resume style:",
                    ["Classic (clean, single-column)", "Modern (sidebar layout)"]
                )
                template_base = "resume_classic" if style_choice.startswith("Classic") else "resume_modern"

                filename = self._generate_resume_pdf_with_template(job_description, template_base)
                
                print(f"✅ Resume generated: {filename}")
                print("📄 Opening resume...")
                
                # Open PDF with default application
                if os.name == 'nt':  # Windows
                    os.startfile(filename)
                elif os.name == 'posix':  # macOS and Linux
                    subprocess.run(['open', filename] if sys.platform == 'darwin' else ['xdg-open', filename])
                
                print("\n✨ Resume opened!")
                
            except Exception as e:
                print(f"❌ Error generating resume: {e}")
                
            # Ask if user wants to generate another resume
            if not self.get_user_choice("Generate another resume?", ["Yes", "No"]) == "Yes":
                break
                
    def _generate_resume_pdf_with_template(self, job_description: str, template_base: str) -> str:
        """Generate PDF from HTML/CSS template via Jinja2 + WeasyPrint."""
        adapted_profile = self._adapt_profile_for_job(job_description)
        relevant_experiences = self._select_relevant_experiences(job_description)
        relevant_skills = self._select_relevant_skills(job_description)

        templates_dir = str(Path(__file__).parent / "templates")
        env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html", "xml"])
        )
        template = env.get_template(f"{template_base}.html")
        html_string = template.render(
            profile=self.profile,
            summary=adapted_profile,
            experiences=relevant_experiences,
            skills=relevant_skills,
        )

        css_path = Path(templates_dir) / f"{template_base}.css"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resume_{timestamp}.pdf"
        HTML(string=html_string, base_url=templates_dir).write_pdf(
            filename,
            stylesheets=[str(css_path)]
        )
        return filename
        
    def _extract_job_title(self, job_description: str) -> str:
        """Extract job title from job description."""
        if not self.client:
            return "Position"
            
        prompt = f"""Extract the job title from this job description. Return ONLY the title, nothing else.

Job Description:
{job_description[:1000]}

Job Title:"""
        
        try:
            response = self.client.generate(prompt)
            return response.strip().replace('\n', ' ')
        except Exception:
            return "Position"
            
    def _adapt_profile_for_job(self, job_description: str) -> str:
        """Adapt profile summary for the specific job."""
        if not self.client:
            return self.profile.get('long_profile', 'Professional with relevant experience.')
            
        prompt = f"""You are a resume writing expert. Write a 4-5 line professional summary for this candidate that highlights their most relevant experience for this specific job.

JOB DESCRIPTION:
{job_description}

CANDIDATE PROFILE:
{self.profile.get('long_profile', '')}

CANDIDATE EXPERIENCES:
{json.dumps(self.profile.get('experiences', []), indent=2)}

Write a compelling summary that matches the job requirements. Return ONLY the summary paragraph."""
        
        try:
            return self.client.generate(prompt)
        except Exception:
            return self.profile.get('long_profile', 'Professional with relevant experience.')
            
    def _select_relevant_experiences(self, job_description: str) -> List[Dict]:
        """Select most relevant experiences for the job."""
        if not self.client:
            return self.profile.get('experiences', [])[:3]
            
        experiences_json = json.dumps(self.profile.get('experiences', []), indent=2)
        
        prompt = f"""You are a resume writing expert. Select the 2-3 MOST relevant experiences for this job and adapt the missions to match the job requirements.

JOB DESCRIPTION:
{job_description}

CANDIDATE EXPERIENCES:
{experiences_json}

Return ONLY a valid JSON array of the most relevant experiences with adapted missions. Use the same structure as the input."""
        
        try:
            response = self.client.generate(prompt)
            start = response.find('[')
            end = response.rfind(']') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return json.loads(response)
        except Exception:
            return self.profile.get('experiences', [])[:3]
            
    def _select_relevant_skills(self, job_description: str) -> Dict[str, List[str]]:
        """Select relevant skills for the job."""
        if not self.client:
            return self.profile.get('skills', {'technical': [], 'soft': []})
            
        skills_json = json.dumps(self.profile.get('skills', {}), indent=2)
        
        prompt = f"""You are a resume writing expert. Select the most relevant skills for this job from the candidate's skills.

JOB DESCRIPTION:
{job_description}

CANDIDATE SKILLS:
{skills_json}

Return ONLY a valid JSON object with 'technical' and 'soft' arrays containing the most relevant skills."""
        
        try:
            response = self.client.generate(prompt)
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return json.loads(response)
        except Exception:
            return self.profile.get('skills', {'technical': [], 'soft': []})
            
        
    def run(self):
        """Main application loop."""
        try:
            self.clear_screen()
            self.print_header("AI RESUME GENERATOR")
            print("Welcome! This tool will help you create tailored resumes using AI.")
            
            # Setup LLM client
            if not self.setup_llm_client():
                print("❌ Failed to setup AI model. Exiting.")
                return
                
            # Create or load profile
            self.create_or_load_profile()
            
            # Main resume generation loop
            self.generate_resume_workflow()
            
            print("\n👋 Thank you for using AI Resume Generator!")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")


def main():
    """Main entry point."""
    app = AIResumeGenerator()
    app.run()


if __name__ == "__main__":
    main()
