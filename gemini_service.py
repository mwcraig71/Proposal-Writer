import os
import json
from typing import Optional
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

AI_INTEGRATIONS_GEMINI_API_KEY = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
AI_INTEGRATIONS_GEMINI_BASE_URL = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")

client = genai.Client(
    api_key=AI_INTEGRATIONS_GEMINI_API_KEY,
    http_options={
        'api_version': '',
        'base_url': AI_INTEGRATIONS_GEMINI_BASE_URL   
    }
)


def is_rate_limit_error(exception: BaseException) -> bool:
    error_msg = str(exception)
    return (
        "429" in error_msg 
        or "RATELIMIT_EXCEEDED" in error_msg
        or "quota" in error_msg.lower() 
        or "rate limit" in error_msg.lower()
        or (hasattr(exception, 'status') and exception.status == 429)
    )


EMPLOYEE_SCHEMA = {
    "name": "string (full name)",
    "title": "string (job title)",
    "role": "string (professional role/discipline)",
    "years_experience_total": "integer (total years of experience)",
    "years_experience_firm": "integer (years with current firm)",
    "education": "string (STANDARDIZED FORMAT: Each degree on new line as 'Degree, Major, Institution (Year)' - Example: 'M.S., Civil Engineering, SUNY Buffalo (1999)\\nB.S., Civil Engineering, SUNY Buffalo (1997)')",
    "registrations": "string (STANDARDIZED FORMAT: Each license on new line as 'License Type #Number, State (Expiration if known)' - Example: 'PE #12345, New York (2025)\\nPE #67890, California')",
    "training": "string (STANDARDIZED FORMAT: Each course on new line as 'Course Name (Year, Course Code)' - Example: 'Safety Inspection of In-Service Bridges (2001, NHI 130055)\\nBridge Inspection Refresher (2020, NHI 130053)')",
    "other_qualifications": "string (certifications, awards, publications - each on new line)",
    "project_experience": [
        {
            "project_title": "string (name of the project)",
            "location": "string (city, state)",
            "owner_name": "string (project owner/client name)",
            "project_cost": "string (project cost/budget if mentioned)",
            "year_completed": "string (year completed or date range)",
            "role_performed": "string (their specific role/function on this project)",
            "brief_description": "string (brief description of the project scope and their contribution)",
            "firm_name": "string (name of the firm/employer where this work was performed)"
        }
    ]
}

STANDARDIZED_FORMAT_INSTRUCTIONS = """
CRITICAL: Apply these EXACT standardized formats:

1. EDUCATION - Each degree on its own line:
   Format: "Degree, Major/Field, Institution (Year)"
   Examples:
   - "Ph.D., Structural Engineering, MIT (2005)"
   - "M.S., Civil Engineering, SUNY Buffalo (1999)"
   - "B.S., Civil Engineering, University of Texas (1995)"

2. REGISTRATIONS/LICENSES - Each license on its own line:
   Format: "License Type #Number, State (Expiration if known)"
   Examples:
   - "PE #12345, New York (2025)"
   - "PE #67890, California"
   - "SE #11111, Illinois (2024)"

3. TRAINING/CERTIFICATIONS - Each course on its own line:
   Format: "Course Name (Year, Course/NHI Code)"
   Examples:
   - "Safety Inspection of In-Service Bridges (2001, NHI 130055)"
   - "Fracture Critical Inspection Techniques (2019, NHI 130078)"
   - "OSHA 30-Hour Construction Safety (2020)"

4. OTHER QUALIFICATIONS - Each item on its own line, grouped by type:
   Format: Free text but organized by category
   Examples:
   - "LEED AP BD+C"
   - "AWS Certified Welding Inspector"
   - "Published: 'Bridge Design Innovations' ASCE Journal, 2018"

Use newline characters (\\n) to separate entries within each field.
"""

PROJECT_SCHEMA = {
    "title": "string (project name)",
    "location": "string (city, state)",
    "year_completed_professional": "string (year professional services completed)",
    "year_completed_construction": "string (year construction completed, if applicable)",
    "owner_name": "string (project owner organization)",
    "owner_contact_name": "string (contact person name)",
    "owner_contact_phone": "string (contact phone number)",
    "project_cost": "string (total project cost)",
    "project_delivery_method": "string (delivery method if mentioned)",
    "brief_description": "string (detailed project description including scope, size, features)",
    "relevance_writeup": "string (why this project is relevant for proposals)",
    "team_members": [
        {
            "name": "string (employee name who worked on this project)",
            "role_on_project": "string (their specific role on this project)"
        }
    ]
}


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception(is_rate_limit_error),
    reraise=True
)
def parse_employee_resume(text: str) -> dict:
    prompt = f"""You are a data extraction assistant for SF330 federal forms. 
Extract employee/personnel information from the following resume or CV text.

Return ONLY valid JSON matching this schema:
{json.dumps(EMPLOYEE_SCHEMA, indent=2)}

{STANDARDIZED_FORMAT_INSTRUCTIONS}

If any field is not found, use null.

IMPORTANT: You MUST follow the standardized formats exactly. Each entry should be on its own line (using \\n).
- Education: "Degree, Major, Institution (Year)"
- Registrations: "License Type #Number, State"
- Training: "Course Name (Year, Code)" - include NHI courses, FHWA training, certifications
- Separate training/continuing education from formal education

PROJECT EXPERIENCE EXTRACTION:
Extract ALL projects mentioned in the resume with as much detail as available:
- project_title: The name of the project
- location: City, State where the project was located
- owner_name: The client/owner organization
- project_cost: Project cost/budget if mentioned (format as currency)
- year_completed: Year completed or date range (e.g., "2020" or "2018-2020")
- role_performed: Their specific role/function on this project (e.g., "Project Manager", "Lead Structural Engineer")
- brief_description: Brief description of the project scope and their specific contribution
- firm_name: The employer/firm where they worked on this project (may differ from current employer)

Include projects from ALL employers mentioned in the resume, not just the current firm.

Text to parse:
{text}

Return ONLY the JSON object, no markdown formatting or explanation."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    result = json.loads(response.text or "{}")
    return result


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception(is_rate_limit_error),
    reraise=True
)
def parse_project_sheet(text: str) -> dict:
    prompt = f"""You are a data extraction assistant for SF330 federal forms.
Extract project information from the following project sheet or description.

Return ONLY valid JSON matching this schema:
{json.dumps(PROJECT_SCHEMA, indent=2)}

If any field is not found, use null. For team_members, extract any personnel mentioned with their roles.
The brief_description should be comprehensive and suitable for SF330 Block 24.

Text to parse:
{text}

Return ONLY the JSON object, no markdown formatting or explanation."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    result = json.loads(response.text or "{}")
    return result


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception(is_rate_limit_error),
    reraise=True
)
def detect_document_type(text: str) -> str:
    prompt = f"""Analyze the following document text and determine if it is primarily:
1. An employee resume/CV (contains personal info, education, experience of one person)
2. A project description/sheet (contains project details, scope, owner, costs)
3. A firm profile (contains company information, address, capabilities)
4. Unknown

Return ONLY one of these exact strings: "employee", "project", "firm", or "unknown"

Text to analyze (first 2000 characters):
{text[:2000]}

Return ONLY the type string, nothing else."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    result = (response.text or "unknown").strip().lower()
    if result not in ["employee", "project", "firm", "unknown"]:
        return "unknown"
    return result


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception(is_rate_limit_error),
    reraise=True
)
def parse_firm_info(text: str) -> dict:
    firm_schema = {
        "name": "string (firm name)",
        "uei": "string (Unique Entity Identifier)",
        "street_address": "string",
        "city": "string",
        "state": "string",
        "zip_code": "string",
        "country": "string (default USA)",
        "year_established": "integer",
        "ownership_type": "string (corporation, partnership, etc.)",
        "is_small_business": "boolean",
        "small_business_categories": "string (8(a), HUBZone, SDVOSB, WOSB, etc.)",
        "phone": "string",
        "fax": "string",
        "email": "string",
        "point_of_contact_name": "string",
        "point_of_contact_title": "string"
    }
    
    prompt = f"""You are a data extraction assistant for SF330 federal forms.
Extract firm/company information from the following text.

Return ONLY valid JSON matching this schema:
{json.dumps(firm_schema, indent=2)}

If any field is not found, use null.

Text to parse:
{text}

Return ONLY the JSON object, no markdown formatting or explanation."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    result = json.loads(response.text or "{}")
    return result


RFP_SCHEMA = {
    "contract_title": "string (the title or name of the contract/project being solicited)",
    "contract_location": "string (city, state or location where work will be performed)",
    "solicitation_number": "string (RFP/RFQ number, solicitation number, or project number)",
    "public_notice_date": "string (date the RFP/RFQ was published, format: YYYY-MM-DD if possible)",
    "submission_deadline": "string (deadline for proposal submission)",
    "agency_name": "string (the agency or organization issuing the RFP/RFQ)",
    "project_description": "string (brief description of the project scope and requirements)",
    "estimated_budget": "string (estimated budget or cost range if mentioned)",
    "required_disciplines": "list of strings (engineering disciplines or expertise required)",
    "naics_codes": "list of strings (NAICS codes if mentioned)",
    "set_aside": "string (small business set-aside type if mentioned: 8(a), HUBZone, SDVOSB, etc.)",
    "evaluation_criteria": "list of strings (key evaluation factors or criteria)"
}


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception(is_rate_limit_error),
    reraise=True
)
def parse_rfp_rfq(text: str) -> dict:
    prompt = f"""You are a data extraction assistant for government RFP/RFQ documents.
Extract key solicitation information from the following Request for Proposal (RFP) or Request for Qualifications (RFQ) document.

Return ONLY valid JSON matching this schema:
{json.dumps(RFP_SCHEMA, indent=2)}

Focus on extracting:
- The contract/project title and location
- Solicitation or project number
- Key dates (publication date, submission deadline)
- Required disciplines and evaluation criteria
- Any set-aside requirements

If any field is not found, use null.

RFP/RFQ text to parse:
{text}

Return ONLY the JSON object, no markdown formatting or explanation."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    result = json.loads(response.text or "{}")
    return result


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception(is_rate_limit_error),
    reraise=True
)
def combine_and_rewrite_text(text1: str, text2: str, field_name: str = "description") -> str:
    """Combine two versions of text and rewrite in a professional structural engineering tone."""
    prompt = f"""You are a professional technical writer specializing in structural engineering documentation for federal SF330 forms.

You have been given two versions of {field_name} text for the same employee or project. Your task is to:
1. Combine the most relevant and accurate information from both versions
2. Eliminate redundancy while preserving all unique details
3. Rewrite the combined text in a professional, concise tone appropriate for federal A/E qualification submissions
4. Use active voice and emphasize technical expertise, project scope, and measurable achievements
5. Keep the format consistent with SF330 requirements

VERSION 1:
{text1 or '(empty)'}

VERSION 2:
{text2 or '(empty)'}

Write a professionally combined version that captures the best of both. Return ONLY the rewritten text, no explanations or formatting markers."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    return (response.text or "").strip()


def find_matching_employee(name: str) -> Optional[int]:
    """Check if an employee with a matching name already exists. Returns employee ID if found."""
    from models import Employee
    import re
    
    if not name:
        return None
    
    normalized_name = ' '.join(name.strip().split()).lower()
    
    all_employees = Employee.query.all()
    for emp in all_employees:
        emp_normalized = ' '.join(emp.name.strip().split()).lower() if emp.name else ''
        if emp_normalized == normalized_name:
            return emp.id
    
    return None


FIRM_WEBSITE_SCHEMA = {
    "name": "string (company/firm name)",
    "street_address": "string (street address if found)",
    "city": "string (city)",
    "state": "string (state abbreviation)",
    "zip_code": "string (ZIP code)",
    "country": "string (country, default USA)",
    "phone": "string (phone number)",
    "fax": "string (fax number if found)",
    "email": "string (email address)",
    "year_established": "integer (year founded/established)",
    "ownership_type": "string (Corporation, Partnership, LLC, etc.)",
    "is_small_business": "boolean (true if small business mentioned)",
    "small_business_categories": "string (8(a), HUBZone, SDVOSB, WOSB, etc.)",
    "point_of_contact_name": "string (primary contact person name)",
    "point_of_contact_title": "string (primary contact title)"
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception(is_rate_limit_error)
)
def parse_firm_website(website_content: str) -> dict:
    """Parse scraped website content to extract firm information using Gemini AI."""
    
    prompt = f"""You are parsing a company/firm website to extract business information for a government form (SF330).

IMPORTANT: Carefully scan ALL sections of the content including headers, footers, contact sections, and about pages.
Look specifically for:
- Phone numbers (often in format xxx-xxx-xxxx or (xxx) xxx-xxxx)
- Email addresses (look for @ symbols)
- Physical addresses (street, city, state, zip)
- Company founding year or "established" dates
- Contact person names and titles

Extract ONLY the information that is clearly present on the website. Do not make up or guess information.

Website content:
{website_content[:20000]}

Extract the following fields if present (return null for missing fields):
{json.dumps(FIRM_WEBSITE_SCHEMA, indent=2)}

Return a valid JSON object with the extracted data. Use null for any field where information is not clearly stated on the website."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    try:
        result = json.loads(response.text)
        return result
    except json.JSONDecodeError:
        return {}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception(is_rate_limit_error)
)
def rewrite_description(description: str, custom_instructions: str = '') -> str:
    """Rewrite a description using AI with global settings and custom instructions."""
    from models import AISettings
    
    style = AISettings.get_value('writing_style', 'professional and technical')
    tone = AISettings.get_value('writing_tone', 'formal but accessible')
    
    prompt = f"""You are a professional technical writer specializing in structural engineering documentation for federal SF330 forms.

Rewrite the following description according to these specifications:

WRITING STYLE: {style}
WRITING TONE: {tone}

{f'CUSTOM INSTRUCTIONS: {custom_instructions}' if custom_instructions else ''}

ORIGINAL DESCRIPTION:
{description}

Rewrite this text while:
1. Maintaining all technical accuracy and key details
2. Using active voice and emphasizing expertise
3. Making it concise yet comprehensive
4. Suitable for federal A/E qualification submissions

Return ONLY the rewritten text, no explanations or formatting markers."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    return (response.text or "").strip()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception(is_rate_limit_error)
)
def generate_cover_letter_ai(
    rfp_text: str,
    firm_name: str,
    firm_bio: str,
    employees: list,
    projects: list,
    contract_title: str,
    solicitation_number: str,
    style: str = '',
    tone: str = '',
    custom_instructions: str = '',
    reference_proposals: str = ''
) -> dict:
    """Generate a cover letter and written sections using RFP + firm + staff + project data."""
    
    employees_summary = '\n'.join([
        f"- {e['name']}: {e.get('title', '')} - {e.get('role_in_contract', '')} ({e.get('years_experience', '')} years experience)"
        for e in employees
    ])
    
    projects_summary = '\n'.join([
        f"- {p['title']}: {p.get('location', '')} for {p.get('owner', '')}"
        for p in projects
    ])
    
    reference_section = ""
    if reference_proposals:
        reference_section = f"""
PREVIOUS PROPOSAL REFERENCES:
The following text is from previously successful proposals. Use these as examples of the firm's writing style, typical project descriptions, and approach language. Adapt relevant content for this specific proposal:

{reference_proposals[:30000]}

---END REFERENCE MATERIALS---
"""
    
    prompt = f"""You are an expert proposal writer for Architect-Engineer (A/E) federal contracts. Generate a professional cover letter and relevant written sections for an SF330 submission.

CONTRACT INFORMATION:
- Title: {contract_title}
- Solicitation Number: {solicitation_number}

FIRM INFORMATION:
- Name: {firm_name}
- Bio: {firm_bio or 'Not provided'}

KEY PERSONNEL:
{employees_summary or 'None selected'}

RELEVANT PROJECTS:
{projects_summary or 'None selected'}

RFP/RFQ REQUIREMENTS (if available):
{rfp_text[:15000] if rfp_text else 'RFP text not available'}
{reference_section}

WRITING SPECIFICATIONS:
- Style: {style or 'Professional and technical'}
- Tone: {tone or 'Formal but accessible'}
{f'- Custom Instructions: {custom_instructions}' if custom_instructions else ''}

Generate the following:

1. COVER LETTER: A professional cover letter (1 page) that:
   - Expresses interest in the contract
   - Highlights the firm's relevant qualifications
   - Summarizes key personnel experience
   - References relevant project experience
   - Demonstrates understanding of the project requirements

2. WRITTEN SECTIONS: Any additional narrative sections commonly required in SF330 submissions such as:
   - Project Understanding/Approach
   - Management Plan
   - Quality Control procedures
   - Relevant Experience summary

Return valid JSON with this structure:
{{
    "cover_letter": "Full cover letter text...",
    "written_sections": "Additional narrative sections..."
}}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    try:
        result = json.loads(response.text or "{}")
        return result
    except json.JSONDecodeError:
        return {
            "cover_letter": response.text or "",
            "written_sections": ""
        }
