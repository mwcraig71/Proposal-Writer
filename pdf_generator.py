import io
import os
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject
from typing import Dict, Any, List, Optional


SF330_TEMPLATE_PATH = "attached_assets/SF330-21a_1769631912450.pdf"

# Field name prefix for the SF330 form
PREFIX = "topmostSubform[0]"


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
        except Exception as e:
            print(f"Error updating page: {e}")
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


def generate_sf330_section_a(proposal_data: Dict[str, Any]) -> Dict[str, str]:
    """Generate Section A - Contract Information (Page 9)"""
    title = proposal_data.get('contract_title', '') or ''
    location = proposal_data.get('contract_location', '') or ''
    title_location = f"{title}"
    if location:
        title_location += f" - {location}"
    
    return {
        f"{PREFIX}.Page9[0].TitleandLocation[0]": title_location,
        f"{PREFIX}.Page9[0].PublicNoticeDate[0]": proposal_data.get("public_notice_date", "") or "",
        f"{PREFIX}.Page9[0].ProjectNumber[0]": proposal_data.get("solicitation_number", "") or "",
    }


def generate_sf330_section_c(firm_data: Dict[str, Any]) -> Dict[str, str]:
    """Generate Section C - Proposed Team (Page 9) - Primary firm info"""
    if not firm_data:
        return {}
    
    name = firm_data.get("name", "") or ""
    street = firm_data.get("street_address", "") or ""
    city = firm_data.get("city", "") or ""
    state = firm_data.get("state", "") or ""
    zip_code = firm_data.get("zip_code", "") or ""
    
    address_parts = [street]
    city_state_zip = ", ".join(filter(None, [city, state]))
    if zip_code:
        city_state_zip += f" {zip_code}"
    if city_state_zip:
        address_parts.append(city_state_zip)
    address = "\n".join(filter(None, address_parts))
    
    return {
        f"{PREFIX}.Page9[0].FirmNameA[0]": name,
        f"{PREFIX}.Page9[0].AddressA[0]": address,
        f"{PREFIX}.Page9[0].RoleinContractA[0]": "Prime Contractor",
        f"{PREFIX}.Page9[0].PrimeA[0]": "1",  # Checkbox for Prime
    }


def generate_sf330_section_d(firm_data: Dict[str, Any]) -> Dict[str, str]:
    """Generate Section D - Organizational Chart / Contact Info (Page 9)"""
    if not firm_data:
        return {}
    
    poc_name = firm_data.get("point_of_contact_name", "") or ""
    poc_title = firm_data.get("point_of_contact_title", "") or ""
    name_title = poc_name
    if poc_title:
        name_title += f", {poc_title}"
    
    return {
        f"{PREFIX}.Page9[0].NameofFirm[0]": firm_data.get("name", "") or "",
        f"{PREFIX}.Page9[0].NameandTitle[0]": name_title,
        f"{PREFIX}.Page9[0].TelephoneNumber[0]": firm_data.get("phone", "") or "",
        f"{PREFIX}.Page9[0].Email[0]": firm_data.get("email", "") or "",
        f"{PREFIX}.Page9[0].FaxNumber[0]": firm_data.get("fax", "") or "",
    }


def generate_sf330_section_e(employee_data: Dict[str, Any], page_num: int = 10) -> Dict[str, str]:
    """Generate Section E - Resume (one per page, starting at Page 10)"""
    page = f"Page{page_num}"
    
    other_qual = employee_data.get("other_qualifications", "") or ""
    training = employee_data.get("training", "") or ""
    combined_qual = f"{other_qual}\n{training}".strip() if training else other_qual
    
    project_experiences = employee_data.get("project_experiences", [])
    
    data = {
        f"{PREFIX}.{page}[0].Name12[0]": employee_data.get("name", "") or "",
        f"{PREFIX}.{page}[0].RoleinContract[0]": employee_data.get("role_in_contract", "") or "",
        f"{PREFIX}.{page}[0].TotalYears[0]": str(employee_data.get("years_experience_total", "") or ""),
        f"{PREFIX}.{page}[0].TotalYearsCurrentFirm[0]": str(employee_data.get("years_experience_firm", "") or ""),
        f"{PREFIX}.{page}[0].FirmName[0]": employee_data.get("firm_name", "") or "",
        f"{PREFIX}.{page}[0].Education[0]": employee_data.get("education", "") or "",
        f"{PREFIX}.{page}[0].CurrentProRegistration[0]": employee_data.get("registrations", "") or "",
        f"{PREFIX}.{page}[0].Qualifications[0]": combined_qual,
    }
    
    # Fill in project experience fields (up to 5 projects per resume page)
    for idx, exp in enumerate(project_experiences[:5]):
        letter = chr(ord('A') + idx)  # A, B, C, D, E
        
        title = exp.get("project_title", "") or ""
        location = exp.get("location", "") or ""
        title_loc = title
        if location:
            title_loc += f" ({location})"
        
        data[f"{PREFIX}.{page}[0].TitleandLocation{letter}[0]"] = title_loc
        
        desc_parts = []
        role = exp.get("role_performed", "")
        if role:
            desc_parts.append(f"Role: {role}")
        owner = exp.get("owner_name", "")
        if owner:
            desc_parts.append(f"Owner: {owner}")
        cost = exp.get("project_cost", "")
        if cost:
            desc_parts.append(f"Cost: {cost}")
        year = exp.get("year_completed", "")
        if year:
            desc_parts.append(f"Year: {year}")
        
        data[f"{PREFIX}.{page}[0].BriefDescription{letter}[0]"] = "; ".join(desc_parts)
        
        # Set checkboxes for project participation
        data[f"{PREFIX}.{page}[0].CheckBox{letter}[0]"] = "1"
    
    return data


def generate_sf330_section_f(project_data: Dict[str, Any]) -> Dict[str, str]:
    """Generate Section F - Example Project (Page 11)"""
    title = project_data.get('title', '') or ''
    location = project_data.get('location', '') or ''
    title_location = title
    if location:
        title_location += f" - {location}"
    
    brief_desc = project_data.get("brief_description", "") or ""
    custom = project_data.get("custom_writeup", "") or ""
    full_desc = brief_desc
    if custom:
        full_desc += "\n\n" + custom
    
    return {
        f"{PREFIX}.Page11[0].TitleandLocation[0]": title_location,
        f"{PREFIX}.Page11[0].ProjectOwner[0]": project_data.get("owner_name", "") or "",
        f"{PREFIX}.Page11[0].PointofContactandTelephone[0]": f"{project_data.get('owner_contact_name', '') or ''} {project_data.get('owner_contact_phone', '') or ''}".strip(),
        f"{PREFIX}.Page11[0].BriefDescriptionandSpecificRole[0]": full_desc,
        f"{PREFIX}.Page11[0].DateCompleted-Actual[0]": project_data.get("year_completed_professional", "") or "",
        f"{PREFIX}.Page11[0].DateCompleted-EstimatedConstruction[0]": project_data.get("year_completed_construction", "") or "",
        f"{PREFIX}.Page11[0].ProjectKey[0]": str(project_data.get("project_key", 1)),
    }


def generate_section_g_matrix(employees: List[Dict], projects: List[Dict], employee_project_links: Dict) -> Dict[str, str]:
    """Generate Section G - Key Personnel Matrix (Page 12)"""
    matrix_data = {}
    
    # Fill employee names (up to 20 rows)
    for emp_idx, employee in enumerate(employees[:20]):
        matrix_data[f"{PREFIX}.Page12[0].NamesofPersonnel[{emp_idx}]"] = employee.get("name", "") or ""
        matrix_data[f"{PREFIX}.Page12[0].RoleinThisContract[{emp_idx}]"] = employee.get("role_in_contract", "") or ""
    
    # Fill project keys (columns 1-10)
    for proj_idx, project in enumerate(projects[:10], 1):
        matrix_data[f"{PREFIX}.Page12[0].ProjectNo[{proj_idx-1}]"] = str(proj_idx)
    
    # Fill the matrix checkboxes
    for emp_idx, employee in enumerate(employees[:20], 1):
        emp_id = employee.get("id")
        for proj_idx, project in enumerate(projects[:10], 1):
            proj_id = project.get("id")
            
            if emp_id in employee_project_links and proj_id in employee_project_links[emp_id]:
                # Checkbox naming: CheckBox{row}-{column}
                checkbox_name = f"{PREFIX}.Page12[0].CheckBox{emp_idx}-{proj_idx}[0]"
                matrix_data[checkbox_name] = "1"
    
    return matrix_data


def generate_sf330_part2(firm_data: Dict[str, Any]) -> Dict[str, str]:
    """Generate Part II - General Qualifications (later pages)"""
    if not firm_data:
        return {}
    
    return {
        # These field names would need to be verified against the actual PDF
        # Part II typically includes firm details, branch offices, etc.
    }


def generate_full_sf330(proposal_data: Dict[str, Any]) -> bytes:
    """Generate complete SF330 PDF with all sections"""
    form_data = {}
    
    # Section A - Contract Information
    form_data.update(generate_sf330_section_a(proposal_data))
    
    # Section C & D - Firm Information
    if proposal_data.get("firm"):
        form_data.update(generate_sf330_section_c(proposal_data["firm"]))
        form_data.update(generate_sf330_section_d(proposal_data["firm"]))
    
    # Section E - Personnel Resumes (one per page starting at page 10)
    # Note: The template may have multiple resume pages or use a single template
    employees = proposal_data.get("employees", [])
    if employees and len(employees) > 0:
        # Fill first resume on Page 10
        form_data.update(generate_sf330_section_e(employees[0], page_num=10))
    
    # Section F - Example Projects (Page 11)
    projects = proposal_data.get("projects", [])
    if projects and len(projects) > 0:
        project_data = projects[0].copy()
        project_data["project_key"] = 1
        form_data.update(generate_sf330_section_f(project_data))
    
    # Section G - Matrix
    if proposal_data.get("employee_project_matrix"):
        form_data.update(generate_section_g_matrix(
            employees,
            projects,
            proposal_data.get("employee_project_matrix", {})
        ))
    
    # Debug: print what we're filling
    print(f"Filling {len(form_data)} form fields")
    for key, value in list(form_data.items())[:10]:
        print(f"  {key}: {value[:50] if isinstance(value, str) and len(value) > 50 else value}")
    
    return fill_pdf_form(form_data)
