# LinkedIn Integration Setup

This guide explains how to set up LinkedIn integration for the AI Resume Generator.

## Overview

The LinkedIn integration allows you to automatically import your professional profile data from LinkedIn, making resume creation faster and more accurate.

## Setup Options

### Option 1: LinkedIn API (Recommended)

For the best experience, you can use LinkedIn's official API with OAuth authentication.

#### Steps:

1. **Create a LinkedIn App:**
   - Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
   - Click "Create App"
   - Fill in the required information:
     - App name: "AI Resume Generator"
     - LinkedIn Page: Your company page (or create one)
     - Privacy policy URL: Your privacy policy
     - App logo: Upload a logo
   - Agree to terms and create the app

2. **Configure OAuth Settings:**
   - In your app settings, go to "Auth" tab
   - Add redirect URL: `http://localhost:8080/callback`
   - Request these scopes:
     - `r_liteprofile` (Basic profile information)
     - `r_emailaddress` (Email address)

3. **Get API Credentials:**
   - Copy your "Client ID" and "Client Secret"
   - Add them to your `.env` file:
     ```
     LINKEDIN_CLIENT_ID=your_client_id_here
     LINKEDIN_CLIENT_SECRET=your_client_secret_here
     ```

4. **Test the Integration:**
   - Run the resume generator: `python main.py`
   - Choose "Import from LinkedIn"
   - Select "Use LinkedIn API (OAuth)"
   - Follow the browser authentication flow

### Option 2: Manual Import (Fallback)

If you don't want to set up the API, you can use the manual import feature.

#### How it works:
1. The system will guide you through entering your LinkedIn information step by step
2. You'll be prompted for:
   - Basic information (name, title, email, etc.)
   - Work experience (job titles, companies, dates, achievements)
   - Education (degrees, schools, dates)
   - Skills (technical and soft skills)
   - Languages

#### Benefits:
- No API setup required
- Works immediately
- You control what information to include
- Can be more selective about what to highlight

## Usage

### Starting LinkedIn Import

1. Run the resume generator:
   ```bash
   python main.py
   ```

2. When prompted for profile creation, choose:
   - "Import from LinkedIn" (if no existing profile)
   - "Import from LinkedIn" (if profile exists)

3. Follow the prompts based on your chosen method

### Data Extracted

The LinkedIn integration extracts:

- **Basic Information:**
  - Full name
  - Current job title
  - Email address
  - Profile picture (if using API)

- **Work Experience:**
  - Job titles and companies
  - Employment dates
  - Job descriptions and achievements
  - Company information

- **Education:**
  - Degrees and fields of study
  - Schools and universities
  - Graduation dates

- **Skills:**
  - Technical skills
  - Endorsed skills
  - Skill categories

- **Additional Information:**
  - Languages
  - Certifications (if available)
  - Volunteer experience (if available)

## Privacy and Security

### Data Handling:
- All data is processed locally on your machine
- No profile data is stored on external servers
- LinkedIn credentials are only used for authentication
- You can review and modify all imported data

### API Permissions:
- The integration only requests basic profile information
- No posting or messaging permissions are requested
- You can revoke access anytime from your LinkedIn settings

## Troubleshooting

### Common Issues:

1. **"LinkedIn API credentials not found"**
   - Make sure your `.env` file contains the correct credentials
   - Verify the Client ID and Secret are correct

2. **"Authorization failed"**
   - Check that your redirect URL matches exactly: `http://localhost:8080/callback`
   - Ensure your app has the correct scopes enabled

3. **"Failed to extract LinkedIn profile data"**
   - Try the manual import option instead
   - Check your internet connection
   - Verify your LinkedIn profile is public or you're logged in

4. **Browser doesn't open for OAuth**
   - Manually copy the authorization URL from the terminal
   - Paste it into your browser

### Getting Help:

If you encounter issues:
1. Try the manual import option first
2. Check the console output for specific error messages
3. Verify your LinkedIn app configuration
4. Ensure all required scopes are enabled

## Best Practices

1. **Review Imported Data:**
   - Always review the imported information
   - Add or modify details as needed
   - Remove any sensitive or irrelevant information

2. **Customize for Each Job:**
   - Use the imported data as a starting point
   - Tailor your resume for each specific job application
   - Highlight relevant experiences and skills

3. **Keep Data Updated:**
   - Re-import from LinkedIn periodically
   - Update your profile with new experiences
   - Maintain consistency across platforms

## Legal Considerations

- Ensure you have permission to use any imported data
- Respect LinkedIn's Terms of Service
- Don't use the integration for unauthorized data collection
- Be mindful of data privacy regulations in your jurisdiction

---

For more information, visit the [LinkedIn Developer Documentation](https://docs.microsoft.com/en-us/linkedin/).
