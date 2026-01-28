import io
import os
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject
from typing import Dict, Any, List, Optional


SF330_TEMPLATE_PATH = "attached_assets/SF330-21a_1769631912450.pdf"


def get_form_fields(pdf_path: str) -> Dict[str, Any]:
    reader = PdfReader(pdf_path)
    fields = {}
    if reader.get_fields():
        for field_name, field_data in reader.get_fields().items():
            fields[field_name] = {
                "type": str(field_data.get("/FT", "Unknown")),
                "value": field_data.get("/V", "")
            }
    return fields


def fill_pdf_form(data: Dict[str, str], output_path: Optional[str] = None) -> bytes:
    if not os.path.exists(SF330_TEMPLATE_PATH):
        raise FileNotFoundError(f"SF330 template not found at {SF330_TEMPLATE_PATH}")
    
    reader = PdfReader(SF330_TEMPLATE_PATH)
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
    
    if "/AcroForm" in writer._root_object:
        writer._root_object["/AcroForm"].update({
            NameObject("/NeedAppearances"): True
        })
    
    for page in writer.pages:
        try:
            writer.update_page_form_field_values(page, data)
        except Exception:
            pass
    
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(output.getvalue())
    
    return output.getvalue()


def format_project_experience(experiences: List[Dict]) -> str:
    """Format project experience entries for Section E Block 19"""
    if not experiences:
        return ""
    
    formatted_entries = []
    for exp in experiences:
        entry_parts = []
        title = exp.get("project_title", "")
        if title:
            entry_parts.append(title)
        
        location = exp.get("location", "")
        if location:
            entry_parts.append(f"({location})")
        
        year = exp.get("year_completed", "")
        if year:
            entry_parts.append(f"[{year}]")
        
        header = " ".join(entry_parts)
        
        role = exp.get("role_performed", "")
        owner = exp.get("owner_name", "")
        cost = exp.get("project_cost", "")
        firm = exp.get("firm_name", "")
        
        details = []
        if role:
            details.append(f"Role: {role}")
        if owner:
            details.append(f"Owner: {owner}")
        if cost:
            details.append(f"Cost: {cost}")
        if firm:
            details.append(f"Firm: {firm}")
        
        entry = header
        if details:
            entry += "\n  " + "; ".join(details)
        
        formatted_entries.append(entry)
    
    return "\n\n".join(formatted_entries)


def generate_sf330_section_e(employee_data: Dict[str, Any], employee_number: int = 1) -> Dict[str, str]:
    prefix = f"E{employee_number}_" if employee_number > 1 else ""
    
    other_qual = employee_data.get("other_qualifications", "") or ""
    training = employee_data.get("training", "") or ""
    combined_other = f"{other_qual}\n{training}".strip() if training else other_qual
    
    project_experiences = employee_data.get("project_experiences", [])
    formatted_experience = format_project_experience(project_experiences)
    
    return {
        f"{prefix}12_Name": employee_data.get("name", ""),
        f"{prefix}13_Role": employee_data.get("role_in_contract", ""),
        f"{prefix}14a_YearsTotal": str(employee_data.get("years_experience_total", "")),
        f"{prefix}14b_YearsFirm": str(employee_data.get("years_experience_firm", "")),
        f"{prefix}15_FirmName": employee_data.get("firm_name", ""),
        f"{prefix}16_Education": employee_data.get("education", ""),
        f"{prefix}17_Registration": employee_data.get("registrations", ""),
        f"{prefix}18_OtherQual": combined_other,
        f"{prefix}19_RelevantProjects": formatted_experience,
    }


def generate_sf330_section_f(project_data: Dict[str, Any], project_number: int = 1) -> Dict[str, str]:
    prefix = f"F{project_number}_" if project_number > 1 else ""
    
    return {
        f"{prefix}20_ProjectKey": str(project_number),
        f"{prefix}21_TitleLocation": f"{project_data.get('title', '')} - {project_data.get('location', '')}",
        f"{prefix}22a_YearProfessional": project_data.get("year_completed_professional", ""),
        f"{prefix}22b_YearConstruction": project_data.get("year_completed_construction", ""),
        f"{prefix}23a_Owner": project_data.get("owner_name", ""),
        f"{prefix}23b_ContactName": project_data.get("owner_contact_name", ""),
        f"{prefix}23c_ContactPhone": project_data.get("owner_contact_phone", ""),
        f"{prefix}24_Description": project_data.get("brief_description", "") + "\n\n" + project_data.get("custom_writeup", ""),
    }


def generate_section_g_matrix(employees: List[Dict], projects: List[Dict], employee_project_links: Dict) -> Dict[str, str]:
    matrix_data = {}
    
    for emp_idx, employee in enumerate(employees, 1):
        matrix_data[f"G_Row{emp_idx}_Name"] = employee.get("name", "")
        matrix_data[f"G_Row{emp_idx}_Role"] = employee.get("role_in_contract", "")
        
        for proj_idx, project in enumerate(projects, 1):
            emp_id = employee.get("id")
            proj_id = project.get("id")
            
            if emp_id in employee_project_links and proj_id in employee_project_links[emp_id]:
                matrix_data[f"G_Row{emp_idx}_Col{proj_idx}"] = "X"
            else:
                matrix_data[f"G_Row{emp_idx}_Col{proj_idx}"] = ""
    
    for proj_idx, project in enumerate(projects, 1):
        matrix_data[f"G_ProjectKey_{proj_idx}"] = str(proj_idx)
        matrix_data[f"G_ProjectTitle_{proj_idx}"] = project.get("title", "")[:50]
    
    return matrix_data


def generate_sf330_part2(firm_data: Dict[str, Any]) -> Dict[str, str]:
    return {
        "2a_FirmName": firm_data.get("name", ""),
        "2b_Street": firm_data.get("street_address", ""),
        "2c_City": firm_data.get("city", ""),
        "2d_State": firm_data.get("state", ""),
        "2e_Zip": firm_data.get("zip_code", ""),
        "3_YearEstablished": str(firm_data.get("year_established", "")),
        "4_UEI": firm_data.get("uei", ""),
        "5a_OwnershipType": firm_data.get("ownership_type", ""),
        "6a_POCName": firm_data.get("point_of_contact_name", ""),
        "6b_POCPhone": firm_data.get("phone", ""),
        "6c_POCEmail": firm_data.get("email", ""),
    }


def generate_full_sf330(proposal_data: Dict[str, Any]) -> bytes:
    form_data = {}
    
    form_data["1_TitleLocation"] = f"{proposal_data.get('contract_title', '')} - {proposal_data.get('contract_location', '')}"
    form_data["2_PublicNoticeDate"] = proposal_data.get("public_notice_date", "")
    form_data["3_SolicitationNumber"] = proposal_data.get("solicitation_number", "")
    
    if proposal_data.get("firm"):
        form_data.update(generate_sf330_part2(proposal_data["firm"]))
    
    for idx, employee in enumerate(proposal_data.get("employees", []), 1):
        form_data.update(generate_sf330_section_e(employee, idx))
    
    for idx, project in enumerate(proposal_data.get("projects", []), 1):
        form_data.update(generate_sf330_section_f(project, idx))
    
    if proposal_data.get("employee_project_matrix"):
        form_data.update(generate_section_g_matrix(
            proposal_data.get("employees", []),
            proposal_data.get("projects", []),
            proposal_data.get("employee_project_matrix", {})
        ))
    
    return fill_pdf_form(form_data)
