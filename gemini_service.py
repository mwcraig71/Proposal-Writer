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
    "other_qualifications": "string (certifications, awards, publications - each on new line)"
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
