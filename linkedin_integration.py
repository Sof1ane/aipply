#!/usr/bin/env python3
"""
LinkedIn Integration Module for Resume Generator

This module provides functionality to extract profile data from LinkedIn
using the official LinkedIn API v2 and web scraping as a fallback.
"""

import os
import json
import requests
import time
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode, parse_qs
import webbrowser
from datetime import datetime

class LinkedInIntegration:
    """LinkedIn integration for profile data extraction."""
    
    def __init__(self):
        self.client_id = os.getenv('LINKEDIN_CLIENT_ID')
        self.client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        self.redirect_uri = 'http://localhost:8080/callback'
        self.scope = 'r_liteprofile r_emailaddress'
        self.api_base = 'https://api.linkedin.com/v2'
        
    def get_authorization_url(self) -> str:
        """Generate LinkedIn OAuth authorization URL."""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': 'resume_generator',
            'scope': self.scope
        }
        return f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> Optional[str]:
        """Exchange authorization code for access token."""
        token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            return token_data.get('access_token')
        except Exception as e:
            print(f"❌ Error exchanging code for token: {e}")
            return None
    
    def get_profile_data(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Fetch profile data from LinkedIn API."""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        try:
            # Get basic profile info
            profile_response = requests.get(
                f'{self.api_base}/people/~',
                headers=headers,
                params={'projection': '(id,firstName,lastName,profilePicture(displayImage~:playableStreams))'}
            )
            profile_response.raise_for_status()
            profile_data = profile_response.json()
            
            # Get email
            email_response = requests.get(
                f'{self.api_base}/emailAddress',
                headers=headers,
                params={'q': 'members', 'projection': '(elements*(handle~))'}
            )
            email_data = email_response.json() if email_response.status_code == 200 else {}
            
            # Get positions (work experience)
            positions_response = requests.get(
                f'{self.api_base}/people/~/positions',
                headers=headers,
                params={'projection': '(elements*(id,title,summary,startDate,endDate,company))'}
            )
            positions_data = positions_response.json() if positions_response.status_code == 200 else {}
            
            # Get education
            education_response = requests.get(
                f'{self.api_base}/people/~/educations',
                headers=headers,
                params={'projection': '(elements*(id,schoolName,degreeName,fieldOfStudy,startDate,endDate))'}
            )
            education_data = education_response.json() if education_response.status_code == 200 else {}
            
            # Get skills
            skills_response = requests.get(
                f'{self.api_base}/people/~/skills',
                headers=headers,
                params={'projection': '(elements*(id,name))'}
            )
            skills_data = skills_response.json() if skills_response.status_code == 200 else {}
            
            return self._structure_linkedin_data(
                profile_data, email_data, positions_data, education_data, skills_data
            )
            
        except Exception as e:
            print(f"❌ Error fetching LinkedIn data: {e}")
            return None
    
    def _structure_linkedin_data(self, profile: Dict, email: Dict, positions: Dict, 
                                education: Dict, skills: Dict) -> Dict[str, Any]:
        """Structure LinkedIn API data into our profile format."""
        
        # Extract basic info
        first_name = profile.get('firstName', {}).get('localized', {}).get('en_US', '')
        last_name = profile.get('lastName', {}).get('localized', {}).get('en_US', '')
        full_name = f"{first_name} {last_name}".strip()
        
        # Extract email
        email_address = ''
        if email.get('elements'):
            email_address = email['elements'][0].get('handle~', {}).get('emailAddress', '')
        
        # Extract work experience
        experiences = []
        if positions.get('elements'):
            for pos in positions['elements']:
                company = pos.get('company', {}).get('name', 'Unknown Company')
                title = pos.get('title', 'Unknown Title')
                summary = pos.get('summary', '')
                
                start_date = pos.get('startDate', {})
                end_date = pos.get('endDate', {})
                
                start_str = f"{start_date.get('month', '')}/{start_date.get('year', '')}" if start_date else ''
                end_str = f"{end_date.get('month', '')}/{end_date.get('year', '')}" if end_date else 'Present'
                
                experiences.append({
                    'role': title,
                    'company': company,
                    'dates': f"{start_str} - {end_str}",
                    'location': '',
                    'missions': [summary] if summary else []
                })
        
        # Extract education
        education_list = []
        if education.get('elements'):
            for edu in education['elements']:
                school = edu.get('schoolName', 'Unknown School')
                degree = edu.get('degreeName', '')
                field = edu.get('fieldOfStudy', '')
                
                start_date = edu.get('startDate', {})
                end_date = edu.get('endDate', {})
                
                start_str = f"{start_date.get('year', '')}" if start_date else ''
                end_str = f"{end_date.get('year', '')}" if end_date else ''
                
                education_list.append({
                    'degree': f"{degree} in {field}".strip(' in'),
                    'school': school,
                    'dates': f"{start_str} - {end_str}".strip(' -')
                })
        
        # Extract skills
        technical_skills = []
        if skills.get('elements'):
            technical_skills = [skill.get('name', '') for skill in skills['elements']]
        
        return {
            "identity": {
                "name": full_name,
                "title": experiences[0]['role'] if experiences else "Professional",
                "email": email_address,
                "phone": "",
                "location": ""
            },
            "long_profile": f"Experienced professional with {len(experiences)} positions at leading companies.",
            "experiences": experiences,
            "education": education_list,
            "skills": {
                "technical": technical_skills,
                "soft": []
            },
            "languages": []
        }
    
    def manual_linkedin_import(self) -> Optional[Dict[str, Any]]:
        """Manual LinkedIn import using web scraping (fallback method)."""
        print("\n🔗 LinkedIn Manual Import")
        print("=" * 50)
        print("Since LinkedIn API requires app registration, we'll use manual import.")
        print("Please provide your LinkedIn profile URL and we'll guide you through data extraction.")
        
        linkedin_url = input("\n📝 Enter your LinkedIn profile URL: ").strip()
        if not linkedin_url:
            print("❌ No URL provided.")
            return None
        
        if 'linkedin.com/in/' not in linkedin_url:
            print("❌ Please provide a valid LinkedIn profile URL (e.g., https://linkedin.com/in/yourname)")
            return None
        
        print(f"\n📋 We'll extract data from: {linkedin_url}")
        print("\n⚠️  Note: This method requires you to manually copy some information.")
        print("We'll guide you through the process step by step.")
        
        # Guide user through manual data entry
        return self._manual_data_entry()
    
    def _manual_data_entry(self) -> Dict[str, Any]:
        """Guide user through manual LinkedIn data entry."""
        print("\n📝 Let's extract your LinkedIn information step by step:")
        
        # Basic information
        name = input("👤 Full Name: ").strip()
        title = input("💼 Current Job Title: ").strip()
        email = input("📧 Email: ").strip()
        phone = input("📱 Phone (optional): ").strip()
        location = input("📍 Location (optional): ").strip()
        
        # Work experience
        print("\n💼 Work Experience:")
        experiences = []
        while True:
            print(f"\nExperience #{len(experiences) + 1}:")
            role = input("  Job Title: ").strip()
            if not role:
                break
            company = input("  Company: ").strip()
            dates = input("  Dates (e.g., 2020 - Present): ").strip()
            location_exp = input("  Location (optional): ").strip()
            
            missions = []
            print("  Key achievements (press Enter when done):")
            while True:
                mission = input("    • ").strip()
                if not mission:
                    break
                missions.append(mission)
            
            experiences.append({
                'role': role,
                'company': company,
                'dates': dates,
                'location': location_exp,
                'missions': missions
            })
            
            if input("\n  Add another experience? (y/n): ").lower() != 'y':
                break
        
        # Education
        print("\n🎓 Education:")
        education = []
        while True:
            print(f"\nEducation #{len(education) + 1}:")
            degree = input("  Degree: ").strip()
            if not degree:
                break
            school = input("  School: ").strip()
            dates = input("  Dates (e.g., 2016 - 2020): ").strip()
            
            education.append({
                'degree': degree,
                'school': school,
                'dates': dates
            })
            
            if input("\n  Add another education? (y/n): ").lower() != 'y':
                break
        
        # Skills
        print("\n🛠️ Skills:")
        technical_skills = input("Technical skills (comma-separated): ").strip()
        technical_skills = [skill.strip() for skill in technical_skills.split(',') if skill.strip()]
        
        soft_skills = input("Soft skills (comma-separated): ").strip()
        soft_skills = [skill.strip() for skill in soft_skills.split(',') if skill.strip()]
        
        # Languages
        print("\n🌍 Languages:")
        languages = input("Languages (comma-separated): ").strip()
        languages = [lang.strip() for lang in languages.split(',') if lang.strip()]
        
        return {
            "identity": {
                "name": name,
                "title": title,
                "email": email,
                "phone": phone,
                "location": location
            },
            "long_profile": f"Experienced {title} with expertise in {', '.join(technical_skills[:3])}.",
            "experiences": experiences,
            "education": education,
            "skills": {
                "technical": technical_skills,
                "soft": soft_skills
            },
            "languages": languages
        }
    
    def start_oauth_flow(self) -> Optional[Dict[str, Any]]:
        """Start LinkedIn OAuth flow for API access."""
        if not self.client_id or not self.client_secret:
            print("❌ LinkedIn API credentials not found.")
            print("Please set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET environment variables.")
            print("Or use the manual import option.")
            return None
        
        print("\n🔗 LinkedIn OAuth Authentication")
        print("=" * 50)
        
        # Open browser for authorization
        auth_url = self.get_authorization_url()
        print(f"🌐 Opening browser for LinkedIn authorization...")
        print(f"📋 If browser doesn't open, visit: {auth_url}")
        
        webbrowser.open(auth_url)
        
        print("\n📝 After authorizing, you'll be redirected to a localhost page.")
        print("Copy the 'code' parameter from the URL and paste it below.")
        
        code = input("\n🔑 Enter the authorization code: ").strip()
        if not code:
            print("❌ No authorization code provided.")
            return None
        
        # Exchange code for token
        print("🔄 Exchanging code for access token...")
        access_token = self.exchange_code_for_token(code)
        if not access_token:
            return None
        
        # Fetch profile data
        print("📥 Fetching LinkedIn profile data...")
        profile_data = self.get_profile_data(access_token)
        
        if profile_data:
            print("✅ LinkedIn profile data extracted successfully!")
            return profile_data
        else:
            print("❌ Failed to extract LinkedIn profile data.")
            return None

def test_linkedin_integration():
    """Test function for LinkedIn integration."""
    linkedin = LinkedInIntegration()
    
    print("🔗 LinkedIn Integration Test")
    print("=" * 50)
    
    # Test manual import
    profile_data = linkedin.manual_linkedin_import()
    
    if profile_data:
        print("\n✅ Profile data extracted:")
        print(f"Name: {profile_data['identity']['name']}")
        print(f"Title: {profile_data['identity']['title']}")
        print(f"Email: {profile_data['identity']['email']}")
        print(f"Experiences: {len(profile_data['experiences'])}")
        print(f"Education: {len(profile_data['education'])}")
        print(f"Skills: {len(profile_data['skills']['technical'])}")
        
        # Save to file
        with open('linkedin_profile.json', 'w') as f:
            json.dump(profile_data, f, indent=2)
        print("\n💾 Profile saved to linkedin_profile.json")
    
    return profile_data

if __name__ == "__main__":
    test_linkedin_integration()
