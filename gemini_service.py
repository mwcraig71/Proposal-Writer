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
    "bio": "string (the introductory biographical paragraph/summary about the person - usually at the top describing their experience and expertise)",
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

DOCUMENT STRUCTURE: The text may be marked with section headers like:
- "=== LEFT COLUMN (CREDENTIALS/QUALIFICATIONS) ===" - Contains education, licenses, training, certifications
- "=== RIGHT COLUMN (BIO AND EXPERIENCE) ===" - Contains bio paragraph and project experience
- "=== DOCUMENT HEADER ===" - May contain name and title

CRITICAL: Extract data from ALL sections. The credentials (education, registrations, training) are typically in the LEFT COLUMN section.

Return ONLY valid JSON matching this schema:
{json.dumps(EMPLOYEE_SCHEMA, indent=2)}

{STANDARDIZED_FORMAT_INSTRUCTIONS}

If any field is not found, use null.

CRITICAL EXTRACTION REQUIREMENTS:

BIO: Extract the FIRST introductory paragraph about the person from the RIGHT COLUMN or HEADER section. This is usually 2-5 sentences describing their overall experience and expertise. Look for text that starts like "[Name] has X years of experience..." or similar. Do NOT use the project list at the end as the bio.

YEARS EXPERIENCE: Look in the LEFT COLUMN for:
- "YEARS WITH [FIRM]" or "YEARS WITH STRINTEG" → years_experience_firm
- "TOTAL YEARS OF EXPERIENCE" → years_experience_total
Extract just the number.

EDUCATION: Look in the LEFT COLUMN for "EDUCATION" section.
Format: "Degree, Major/Field, Institution (Year)"
Examples from document:
- "B.S. Civil Engineering: SUNY Buffalo, 1997" → "B.S., Civil Engineering, SUNY Buffalo (1997)"
- "M.ENG. Structural: SUNY Buffalo, 1999" → "M.Eng., Structural Engineering, SUNY Buffalo (1999)"

REGISTRATIONS: Look in the LEFT COLUMN for "PROFESSIONAL REGISTRATIONS" section.
Include ALL licenses. Format each on a new line.
Examples:
- "Structural Engineer: GA (000958)" → "SE #000958, Georgia"
- "Professional Engineer: AL, DC, FL, GA, KS, LA, MD, NC, NE, NV, PR, SC, TN, TX, VA" → List as "PE, Alabama\\nPE, District of Columbia\\nPE, Florida\\n..." etc.
- "Level 1 Rope Access Technician" → "Level 1 Rope Access Technician"
- "FAA Part 107 UAS Remote Pilot" → "FAA Part 107 UAS Remote Pilot"

TRAINING: Look in the LEFT COLUMN for "PROFESSIONAL TRAINING" section.
Format: "Course Name (Year, Course Code)"
Include ALL NHI courses and training:
- "Safety Inspection of In-Service Bridges (Course No. 130055), National Highway Institute, 2021 & Refresher (2023)" → "Safety Inspection of In-Service Bridges (2021, NHI 130055)\\nSafety Inspection of In-Service Bridges Refresher (2023, NHI 130055)"
- "Fracture Critical Inspection Techniques for Steel Bridges (NHI 130078)" → "Fracture Critical Inspection Techniques for Steel Bridges (NHI 130078)"

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


MULTI_PROJECT_SCHEMA = {
    "projects": [
        {
            "contract_number": "string (contract or project number/ID)",
            "title": "string (project name or contract title)",
            "location": "string (city, state where work was performed)",
            "client": "string (client organization name)",
            "primary_contact_name": "string (primary reference contact name)",
            "primary_contact_phone": "string (primary contact phone number)",
            "primary_contact_email": "string (primary contact email)",
            "alternate_contact_name": "string (alternate reference contact name)",
            "alternate_contact_phone": "string (alternate contact phone number)", 
            "alternate_contact_email": "string (alternate contact email)",
            "contract_value": "string (contract value/cost)",
            "year_completed": "string (year completed or date range)",
            "delivery_method": "string (project delivery method if mentioned)",
            "description": "string (description of work performed)"
        }
    ]
}


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception(is_rate_limit_error),
    reraise=True
)
def parse_multiple_projects(text: str) -> dict:
    """Parse a document containing multiple projects in table or list format (like a references sheet)."""
    prompt = f"""You are a data extraction assistant for SF330 federal forms.
Extract ALL project/contract references from the following document. This document contains multiple projects in a table or list format (often a references appendix or project experience table).

Return ONLY valid JSON matching this schema:
{json.dumps(MULTI_PROJECT_SCHEMA, indent=2)}

EXTRACTION GUIDELINES:
1. Extract EVERY project/contract mentioned in the document
2. For each project, capture:
   - Contract/project number or ID
   - Project title or contract name  
   - Location (city, state)
   - Client/owner organization
   - Primary contact name, phone, and email
   - Alternate contact name, phone, and email (if provided)
   - Contract value/cost
   - Year completed or date range
   - Delivery method (if mentioned)
   - Description of work performed
3. If a field is not found for a project, use null
4. Parse phone numbers in format: xxx-xxx-xxxx
5. Capture the full description of work for each project

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
    
    result = json.loads(response.text or '{"projects": []}')
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
2. A project description/sheet (contains details about a SINGLE project - scope, owner, costs)
3. A project references table (contains MULTIPLE projects/contracts listed in a table or list format, often with contact info and contract values - like a references appendix)
4. A firm profile (contains company information, address, capabilities)
5. Unknown

Return ONLY one of these exact strings: "employee", "project", "projects", "firm", or "unknown"
- Return "project" for a SINGLE project description
- Return "projects" for MULTIPLE projects in a table/list format (references appendix)

Text to analyze (first 2000 characters):
{text[:2000]}

Return ONLY the type string, nothing else."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    result = (response.text or "unknown").strip().lower()
    if result not in ["employee", "project", "projects", "firm", "unknown"]:
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


PORTFOLIO_PROJECT_SCHEMA = {
    "projects": [
        {
            "title": "string (project name)",
            "location": "string (city, state)",
            "client": "string (owner/client organization)",
            "year_completed": "string (year or date range like 2021-2023)",
            "contract_value": "string (cost if mentioned)",
            "description": "string (full description of work performed)"
        }
    ]
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception(is_rate_limit_error)
)
def parse_portfolio_projects(website_content: str) -> dict:
    """Parse scraped portfolio website content to extract project information."""
    
    prompt = f"""You are parsing a company portfolio/experience website to extract project information for SF330 forms.

Extract ALL projects mentioned in the content. For each project, capture:
- Project title/name
- Location (city, state)
- Client/owner organization (often a DOT or government agency)
- Year completed or date range
- Contract value if mentioned
- Full description of work performed

Website content:
{website_content[:30000]}

Return ONLY valid JSON matching this schema:
{json.dumps(PORTFOLIO_PROJECT_SCHEMA, indent=2)}

IMPORTANT:
1. Extract every distinct project mentioned
2. Use null for missing fields
3. Capture the full description for each project
4. Look for patterns like "Client:", "Owner:", dates in parentheses, dollar amounts"""

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
        return {"projects": []}


TEAM_PERSONNEL_SCHEMA = {
    "type": "object",
    "properties": {
        "personnel": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "title": {"type": "string"},
                    "role": {"type": "string"},
                    "education": {"type": "string"},
                    "registrations": {"type": "string"},
                    "bio": {"type": "string"},
                    "years_experience": {"type": "integer"}
                },
                "required": ["name"]
            }
        }
    }
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception(is_rate_limit_error)
)
def parse_team_personnel(website_content: str) -> dict:
    """Parse scraped team/about website content to extract personnel information."""
    
    prompt = f"""You are parsing a company team/about page to extract personnel information for SF330 forms.

Extract ALL team members mentioned. For each person, capture:
- Full name
- Job title (e.g., "Senior Structural Engineer", "Project Manager")
- Role/discipline (e.g., "Structural Engineering", "Bridge Inspection")
- Education (degrees, institutions, years if mentioned)
- Professional registrations (PE licenses, certifications)
- Biography/summary of experience
- Years of experience if mentioned

Website content:
{website_content[:30000]}

Return ONLY valid JSON matching this schema:
{json.dumps(TEAM_PERSONNEL_SCHEMA, indent=2)}

IMPORTANT:
1. Extract every distinct team member mentioned
2. Use null for missing fields
3. For education, format as: "Degree, Major, Institution (Year)" - one per line
4. For registrations, format as: "License Type #Number, State" - one per line
5. Capture full bio/experience text for each person"""

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
        return {"personnel": []}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception(is_rate_limit_error)
)
def merge_field_values(field_key: str, values: list) -> str:
    """Merge multiple field values into one using AI."""
    from models import AISettings
    
    style = AISettings.get_value('writing_style', 'professional and technical')
    tone = AISettings.get_value('writing_tone', 'formal but accessible')
    
    field_labels = {
        'project_title': 'Project Title',
        'location': 'Location',
        'owner_name': 'Owner/Client',
        'project_cost': 'Project Cost',
        'year_completed': 'Year Completed',
        'role_performed': 'Role Performed',
        'firm_name': 'Firm Name',
        'brief_description': 'Project Description'
    }
    
    field_label = field_labels.get(field_key, field_key)
    is_description = field_key == 'brief_description'
    
    values_text = '\n'.join([f"Value {i+1}: {v}" for i, v in enumerate(values)])
    
    if is_description:
        prompt = f"""You are a professional technical writer for SF330 Architect-Engineer Qualifications forms.

Merge these project descriptions into ONE comprehensive description:

WRITING STYLE: {style}
WRITING TONE: {tone}

{values_text}

Create a single merged description that:
1. Combines all key information from each description
2. Eliminates redundancy
3. Maintains technical accuracy
4. Is suitable for federal A/E qualification submissions
5. Is 200-400 words

Return ONLY the merged description text, no explanations."""
    else:
        prompt = f"""Merge these {field_label} values into one concise combined value:

{values_text}

Rules:
- For locations: combine if different, or use the most specific
- For costs: show range if different, or combine totals
- For years: show range (e.g., "2018-2023") if different
- For names: combine with commas or slashes if different
- Keep it concise

Return ONLY the merged value, no explanations."""

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
def merge_project_experiences(experiences: list, custom_instructions: str = '') -> dict:
    """Merge multiple project experiences into one using AI."""
    from models import AISettings
    
    style = AISettings.get_value('writing_style', 'professional and technical')
    tone = AISettings.get_value('writing_tone', 'formal but accessible')
    
    projects_text = ""
    for i, exp in enumerate(experiences, 1):
        projects_text += f"""
PROJECT {i}:
- Title: {exp.project_title or 'N/A'}
- Location: {exp.location or 'N/A'}
- Owner: {exp.owner_name or 'N/A'}
- Cost: {exp.project_cost or 'N/A'}
- Year: {exp.year_completed or 'N/A'}
- Role: {exp.role_performed or 'N/A'}
- Firm: {exp.firm_name or 'N/A'}
- Description: {exp.brief_description or 'N/A'}
"""

    prompt = f"""You are a professional technical writer for SF330 Architect-Engineer Qualifications forms.

Merge the following {len(experiences)} project experiences into ONE combined project entry. These may be related phases, similar work, or projects that should be combined for a resume.

WRITING STYLE: {style}
WRITING TONE: {tone}

{f'CUSTOM INSTRUCTIONS: {custom_instructions}' if custom_instructions else ''}

{projects_text}

Create ONE merged project entry. Return a JSON object with these fields:
- project_title: Combined/representative title
- location: Combined location(s) or most representative
- owner_name: Combined owner(s) or most representative
- project_cost: Combined cost or range
- year_completed: Year range or most recent
- role_performed: Combined roles
- firm_name: Firm name (if consistent)
- brief_description: Merged description highlighting all work performed (250-400 words)

Return ONLY valid JSON, no markdown or explanations."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    import json
    import re
    text = (response.text or "").strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            'project_title': experiences[0].project_title,
            'brief_description': text
        }


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
    reference_proposals: str = '',
    org_chart_data: str = '',
    org_chart_notes: str = '',
    proposal_outline: str = ''
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
    
    org_chart_section = ""
    if org_chart_data:
        try:
            chart_json = json.loads(org_chart_data)
            nodes = chart_json.get('nodes', [])
            org_structure = []
            for node in nodes:
                data = node.get('data', {})
                role = data.get('role', '')
                assigned_staff = data.get('assignedStaff', '')
                staff_list = data.get('staffList', [])
                if role:
                    if assigned_staff:
                        org_structure.append(f"- {role}: {assigned_staff}")
                    elif staff_list:
                        org_structure.append(f"- {role}: {', '.join(staff_list)}")
                    else:
                        org_structure.append(f"- {role}: (Unassigned)")
            
            if org_structure:
                org_chart_section = f"""
PROJECT ORGANIZATIONAL STRUCTURE:
The following is the project's organizational chart showing team structure and role assignments:

{chr(10).join(org_structure)}
{f'{chr(10)}Notes: {org_chart_notes}' if org_chart_notes else ''}

Use this organizational structure to describe the management approach and team composition in the proposal.
---END ORG CHART---
"""
        except (json.JSONDecodeError, KeyError):
            pass
    
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
{org_chart_section}
{f'''
PROPOSAL OUTLINE (IMPORTANT - Use this as your primary guide):
The following outline was created to guide the proposal writing. Follow its themes, emphasis areas, and win strategies closely:

{proposal_outline[:10000]}

---END PROPOSAL OUTLINE---
''' if proposal_outline else ''}
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


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception(is_rate_limit_error)
)
def generate_proposal_outline_ai(
    rfp_text: str,
    firm_name: str,
    firm_bio: str,
    employees: list,
    projects: list,
    contract_title: str,
    solicitation_number: str,
    custom_instructions: str = '',
    org_chart_data: str = '',
    org_chart_notes: str = '',
    linked_responses: list = None,
    linked_references: list = None
) -> str:
    """Generate a proposal outline based on RFP requirements and all linked proposal data."""
    
    employees_summary = []
    pm_info = []
    senior_leaders = []
    
    for e in employees:
        role = e.get('role_in_contract', '').upper()
        emp_line = f"- {e['name']}: {e.get('title', '')} - {e.get('role_in_contract', '')} ({e.get('years_experience', '')} years experience)"
        employees_summary.append(emp_line)
        
        if 'PM' in role or 'PROJECT MANAGER' in role or 'PRINCIPAL' in role:
            pm_info.append(f"  * {e['name']}: {e.get('title', '')} with {e.get('years_experience', '')} years experience. {e.get('bio', '')[:500] if e.get('bio') else ''}")
        elif 'LEADER' in role or 'DPM' in role or 'QA' in role or 'MANAGER' in role:
            senior_leaders.append(f"  * {e['name']}: {e.get('role_in_contract', '')} with {e.get('years_experience', '')} years experience")
    
    projects_summary = '\n'.join([
        f"- {p['title']}: {p.get('location', '')} for {p.get('owner', '')}"
        for p in projects
    ])
    
    org_chart_section = ""
    if org_chart_data:
        try:
            chart_json = json.loads(org_chart_data)
            nodes = chart_json.get('nodes', [])
            org_structure = []
            for node in nodes:
                data = node.get('data', {})
                role = data.get('role', '')
                assigned_staff = data.get('assignedStaff', '')
                staff_list = data.get('staffList', [])
                if role:
                    if assigned_staff:
                        org_structure.append(f"  - {role}: {assigned_staff}")
                    elif staff_list:
                        org_structure.append(f"  - {role}: {', '.join(staff_list)}")
            
            if org_structure:
                org_chart_section = f"""
PROJECT TEAM STRUCTURE:
{chr(10).join(org_structure)}
{f'Team Notes: {org_chart_notes}' if org_chart_notes else ''}
"""
        except (json.JSONDecodeError, KeyError):
            pass
    
    responses_section = ""
    if linked_responses:
        responses_section = "LINKED RESPONSE LIBRARY CONTENT:\n"
        for r in linked_responses[:5]:
            responses_section += f"- {r.get('question', '')[:100]}: {r.get('response', '')[:300]}...\n"
    
    references_section = ""
    if linked_references:
        references_section = "PERFORMANCE REFERENCES:\n"
        for ref in linked_references[:5]:
            references_section += f"- {ref.get('project_name', '')}: Score {ref.get('final_score', 'N/A')} - {ref.get('client', '')}\n"
    
    prompt = f"""You are an expert proposal strategist for Architect-Engineer (A/E) federal contracts. Create a detailed PROPOSAL OUTLINE that will guide the writing of a winning SF330 submission.

CONTRACT INFORMATION:
- Title: {contract_title}
- Solicitation Number: {solicitation_number}

FIRM INFORMATION:
- Name: {firm_name}
- Bio: {firm_bio[:2000] if firm_bio else 'Not provided'}

PROJECT MANAGER AND SENIOR LEADERSHIP EXPERIENCE:
{chr(10).join(pm_info) if pm_info else 'PM not yet designated'}

OTHER SENIOR TEAM LEADERS:
{chr(10).join(senior_leaders) if senior_leaders else 'None identified'}

FULL TEAM:
{chr(10).join(employees_summary) or 'None selected'}

RELEVANT PROJECTS:
{projects_summary or 'None selected'}
{org_chart_section}
{responses_section}
{references_section}

RFP/RFQ REQUIREMENTS:
{rfp_text[:20000] if rfp_text else 'RFP text not available - create a general outline for an engineering services proposal'}

{f'CUSTOM INSTRUCTIONS FROM USER: {custom_instructions}' if custom_instructions else ''}

Generate a comprehensive PROPOSAL OUTLINE that includes:

1. EXECUTIVE SUMMARY OUTLINE
   - Key win themes (3-5 compelling differentiators)
   - Primary message to convey
   
2. UNDERSTANDING OF THE PROJECT
   - Key requirements identified from RFP
   - Technical challenges to address
   - Approach themes
   
3. MANAGEMENT APPROACH OUTLINE
   - How to highlight PM's relevant experience with this client or similar work
   - Team structure messaging
   - Communication and coordination approach
   
4. TECHNICAL APPROACH OUTLINE
   - Key technical themes to emphasize
   - Innovative approaches or methodologies
   - Quality control highlights
   
5. RELEVANT EXPERIENCE THEMES
   - How to tie projects to this contract
   - Specific accomplishments to highlight
   - Client relationship experience to emphasize
   
6. KEY PERSONNEL EMPHASIS
   - Specific experience to highlight for PM and senior leaders
   - Client relationship history to mention
   - Technical expertise differentiators
   
7. WIN STRATEGY NOTES
   - What makes this team uniquely qualified
   - Potential weaknesses to mitigate
   - Evaluation criteria alignment

Format this as a clear, actionable outline that can guide the writing of cover letter and written sections. Use bullet points and clear headings."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    return response.text or ""
