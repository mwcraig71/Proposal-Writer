"""
SF330 Word Document Generator
Generates filled SF330 Word documents from proposal data
"""
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import copy
import io
import os

TEMPLATE_DIR = 'templates/sf330_word'

def get_cell_text(table, row, col):
    """Safely get cell text"""
    try:
        return table.rows[row].cells[col].text.strip()
    except:
        return ""

def set_cell_text(table, row, col, text):
    """Set cell text, preserving formatting"""
    try:
        if row >= len(table.rows) or col >= len(table.rows[row].cells):
            return
        cell = table.rows[row].cells[col]
        text_str = str(text) if text else ""
        if cell.paragraphs:
            for run in cell.paragraphs[0].runs:
                run.text = ""
            if cell.paragraphs[0].runs:
                cell.paragraphs[0].runs[0].text = text_str
            else:
                cell.paragraphs[0].add_run(text_str)
        else:
            cell.text = text_str
    except Exception as e:
        print(f"Error setting cell [{row}][{col}]: {e}")

def generate_section_a_c(proposal, firms):
    """
    Generate Section A (Contract Info), B (POC), C (Proposed Team)
    Returns: Document object
    """
    doc = Document(os.path.join(TEMPLATE_DIR, 'section_a_c.docx'))
    table = doc.tables[0]
    
    # Section A - Contract Information
    # Row 3: Title and Location (spans full width, data goes in second row after label)
    title_location = f"{proposal.contract_title or ''}"
    if proposal.contract_location:
        title_location += f" ({proposal.contract_location})"
    
    # Find the cells for each field by examining the structure
    # Row 3 has the label, need to find where to put data
    # Based on SF330 structure, data typically goes in cells below or adjacent to labels
    
    # For this template, we need to identify exact cell positions
    # Row 3: Title and Location label - data goes below
    # Row 4: Public Notice Date | Solicitation Number
    
    # Set contract title/location (in the row content area)
    set_cell_text(table, 3, 0, f"1.  TITLE AND LOCATION (City and State)\n{title_location}")
    
    # Row 4: Public Notice Date and Solicitation Number
    if proposal.public_notice_date:
        if hasattr(proposal.public_notice_date, 'strftime'):
            notice_date = proposal.public_notice_date.strftime('%m/%d/%Y')
        else:
            notice_date = str(proposal.public_notice_date)
    else:
        notice_date = ""
    set_cell_text(table, 4, 0, f"2.  PUBLIC NOTICE DATE\n{notice_date}")
    set_cell_text(table, 4, 8, f"3.  SOLICITATION OR PROJECT NUMBER\n{proposal.solicitation_number or ''}")
    
    # Section B - Point of Contact (primary firm)
    if proposal.firm:
        firm = proposal.firm
        poc_name = getattr(firm, 'point_of_contact_name', '') or getattr(firm, 'contact_name', '') or ''
        poc_title = getattr(firm, 'point_of_contact_title', '') or ''
        poc_display = f"{poc_name}, {poc_title}" if poc_title else poc_name
        # Row 5-6: POC section
        set_cell_text(table, 6, 0, f"4.  NAME AND TITLE\n{poc_display}")
        set_cell_text(table, 7, 0, f"5.  NAME OF FIRM\n{firm.name or ''}")
        set_cell_text(table, 8, 0, f"6.  TELEPHONE NUMBER\n{getattr(firm, 'phone', '') or ''}")
        set_cell_text(table, 8, 4, f"7.  FAX NUMBER\n{getattr(firm, 'fax', '') or ''}")
        set_cell_text(table, 8, 7, f"8.  E-MAIL ADDRESS\n{getattr(firm, 'email', '') or ''}")
    
    # Section C - Proposed Team (rows 12-17 typically for team members)
    # The table has rows for up to 6 firms (a through f)
    team_start_row = 12  # Approximate start for team entries
    
    for idx, firm_data in enumerate(firms[:6]):
        row_offset = team_start_row + idx
        if row_offset < len(table.rows):
            firm = firm_data.get('firm')
            role = firm_data.get('role', '')
            is_prime = firm_data.get('is_prime', False)
            
            if firm:
                # Set firm name
                address = f"{firm.city}, {firm.state}" if firm.city and firm.state else ""
                set_cell_text(table, row_offset, 4, firm.name or '')
                set_cell_text(table, row_offset, 7, address)
                set_cell_text(table, row_offset, 9, role)
    
    return doc


def generate_section_e(employee, proposal, project_experiences):
    """
    Generate Section E (Resume) for one employee
    Returns: Document object
    """
    doc = Document(os.path.join(TEMPLATE_DIR, 'section_e.docx'))
    table = doc.tables[0]
    
    # Row 0: Header
    # Row 1: Name | Role | Years Experience
    set_cell_text(table, 1, 0, employee.name or '')
    
    role = ""
    if hasattr(employee, 'proposal_role'):
        role = employee.proposal_role
    set_cell_text(table, 1, 2, role)
    
    # Years experience
    years_total = employee.years_experience or ""
    years_firm = employee.years_with_firm or ""
    set_cell_text(table, 1, 4, str(years_total))
    set_cell_text(table, 1, 5, str(years_firm))
    
    # Row 2: Firm Name and Location
    if proposal.firm:
        firm_loc = f"{proposal.firm.name}, {proposal.firm.city}, {proposal.firm.state}"
        set_cell_text(table, 2, 0, firm_loc)
    
    # Row 3: Education
    set_cell_text(table, 3, 0, employee.education or '')
    
    # Row 3 right side: Professional Registration
    set_cell_text(table, 3, 3, employee.registrations or '')
    
    # Row 4: Other Professional Qualifications
    other_quals = ""
    if employee.training:
        other_quals += employee.training
    if employee.other_qualifications:
        if other_quals:
            other_quals += "\n"
        other_quals += employee.other_qualifications
    set_cell_text(table, 4, 0, other_quals)
    
    # Rows 5-29: Relevant Projects (5 projects, each takes ~5 rows)
    project_row_starts = [7, 12, 17, 22, 27]  # Approximate row starts for projects a-e
    
    for idx, exp in enumerate(project_experiences[:5]):
        if idx < len(project_row_starts):
            start_row = project_row_starts[idx]
            
            # Project title and location
            title_loc = exp.title or ''
            if exp.location:
                title_loc += f", {exp.location}"
            
            if start_row < len(table.rows):
                set_cell_text(table, start_row, 0, title_loc)
                
                # Year completed
                set_cell_text(table, start_row, 4, str(exp.year_completed or ''))
                
                # Brief description
                desc_row = start_row + 1
                if desc_row < len(table.rows):
                    description = exp.description or ''
                    if exp.role:
                        description += f"\nRole: {exp.role}"
                    set_cell_text(table, desc_row, 0, description)
    
    return doc


def generate_section_f(project, proposal, project_key_number, firms_involved=None):
    """
    Generate Section F (Example Project) for one project
    Returns: Document object
    """
    doc = Document(os.path.join(TEMPLATE_DIR, 'section_f.docx'))
    
    # Table 0: Main project info
    table = doc.tables[0]
    
    # Project Key Number (Block 20)
    set_cell_text(table, 0, 7, str(project_key_number))
    
    # Title and Location (Block 21)
    title_loc = project.title or ''
    if project.location:
        title_loc += f", {project.location}"
    set_cell_text(table, 1, 0, title_loc)
    
    # Year Completed (Block 22) - use professional services year
    year_completed = getattr(project, 'year_completed_professional', '') or getattr(project, 'year_completed', '') or ''
    set_cell_text(table, 1, 5, str(year_completed))
    
    # Project Owner Info (Block 23)
    set_cell_text(table, 3, 0, getattr(project, 'owner_name', '') or '')
    set_cell_text(table, 3, 3, getattr(project, 'owner_contact_name', '') or '')
    set_cell_text(table, 3, 6, getattr(project, 'owner_contact_phone', '') or '')
    
    # Brief Description (Block 24) - large text area
    description = project.brief_description or ''
    set_cell_text(table, 4, 0, description)
    
    # Table 1: Firms involved (Block 25)
    if len(doc.tables) > 1 and firms_involved:
        firms_table = doc.tables[1]
        for idx, firm_info in enumerate(firms_involved[:6]):
            row_idx = idx + 1  # Skip header row
            if row_idx < len(firms_table.rows):
                firm = firm_info.get('firm')
                if firm:
                    set_cell_text(firms_table, row_idx, 1, firm.name or '')
                    loc = f"{firm.city}, {firm.state}" if firm.city else ""
                    set_cell_text(firms_table, row_idx, 3, loc)
                    set_cell_text(firms_table, row_idx, 5, firm_info.get('role', ''))
    
    return doc


def generate_section_g(employees_with_roles, projects, matrix):
    """
    Generate Section G (Key Personnel Participation Matrix)
    matrix: dict of {employee_id: set(project_ids)} 
    Returns: Document object
    """
    doc = Document(os.path.join(TEMPLATE_DIR, 'section_g.docx'))
    table = doc.tables[0]
    
    # Row 0-2: Headers
    # Row 2: Project numbers 1-10
    # Starting from row 3: Employee rows
    
    # Set project titles in header (columns 2-11 for projects 1-10)
    # The bottom of the section has project key titles
    
    # Fill employee rows (starting at row 3)
    for emp_idx, emp_data in enumerate(employees_with_roles[:19]):  # Max 19 employees
        row_idx = emp_idx + 3
        if row_idx < len(table.rows) - 10:  # Leave room for footer
            employee = emp_data.get('employee')
            role = emp_data.get('role', '')
            
            set_cell_text(table, row_idx, 0, employee.name if employee else '')
            set_cell_text(table, row_idx, 1, role)
            
            # Mark X for projects where employee participated
            if employee:
                emp_projects = matrix.get(employee.id, set())
                for proj_idx, project in enumerate(projects[:10]):
                    if project.id in emp_projects:
                        # Columns 2-11 are for projects 1-10
                        set_cell_text(table, row_idx, proj_idx + 2, "X")
    
    # Set project titles at bottom (Example Projects Key section)
    # This is typically rows 22-26 or similar
    footer_start = len(table.rows) - 7
    for proj_idx, project in enumerate(projects[:10]):
        if proj_idx < 5:
            row = footer_start + proj_idx
            if row < len(table.rows):
                set_cell_text(table, row, 1, project.title or '')
        else:
            row = footer_start + (proj_idx - 5)
            if row < len(table.rows):
                set_cell_text(table, row, 8, project.title or '')
    
    return doc


def generate_section_h(proposal, additional_info=""):
    """
    Generate Section H (Additional Information) and I (Signature)
    Returns: Document object
    """
    doc = Document(os.path.join(TEMPLATE_DIR, 'section_h_i.docx'))
    
    # Section H is mostly in paragraphs, not tables
    # Find and fill the additional info area
    for para in doc.paragraphs:
        if "30." in para.text or "ADDITIONAL INFORMATION" in para.text:
            # Add content after this paragraph
            continue
    
    # The written sections go here
    content = proposal.written_sections or additional_info or ""
    if doc.paragraphs:
        # Find appropriate paragraph to add content
        for i, para in enumerate(doc.paragraphs):
            if para.text.strip() == "" and i > 5:  # Find empty paragraph after header
                para.text = content
                break
    
    # Table 1 has signature info
    if len(doc.tables) > 1:
        sig_table = doc.tables[1]
        # Signature date
        from datetime import datetime
        set_cell_text(sig_table, 0, 1, datetime.now().strftime('%m/%d/%Y'))
        
        # Name and title
        if proposal.firm:
            poc_name = getattr(proposal.firm, 'point_of_contact_name', '') or ''
            poc_title = getattr(proposal.firm, 'point_of_contact_title', '') or ''
            poc_display = f"{poc_name}, {poc_title}" if poc_title else poc_name
            set_cell_text(sig_table, 2, 0, poc_display)
    
    return doc


def generate_part_ii(firm):
    """
    Generate Part II (General Qualifications)
    Returns: Document object
    """
    doc = Document(os.path.join(TEMPLATE_DIR, 'part_ii.docx'))
    table = doc.tables[0]
    
    # Row 1: Firm name | Year Established | UEI
    set_cell_text(table, 2, 0, firm.name or '')  # Block 2a
    set_cell_text(table, 2, 7, str(firm.year_established or ''))  # Block 3
    set_cell_text(table, 2, 10, firm.uei or '')  # Block 4
    
    # Row 3-5: Street, City, State, ZIP
    set_cell_text(table, 4, 0, firm.street_address or '')  # Block 2b
    set_cell_text(table, 6, 0, firm.city or '')  # Block 2c
    set_cell_text(table, 6, 4, firm.state or '')  # Block 2d
    set_cell_text(table, 6, 7, firm.zip_code or '')  # Block 2e
    
    # Ownership type
    set_cell_text(table, 4, 7, firm.ownership_type or '')  # Block 5a
    
    # Point of Contact (Block 6)
    poc_name = getattr(firm, 'point_of_contact_name', '') or ''
    poc_title = getattr(firm, 'point_of_contact_title', '') or ''
    poc_display = f"{poc_name}, {poc_title}" if poc_title else poc_name
    set_cell_text(table, 10, 0, poc_display)  # Block 6a
    set_cell_text(table, 12, 0, getattr(firm, 'phone', '') or '')  # Block 6b
    set_cell_text(table, 12, 7, getattr(firm, 'email', '') or '')  # Block 6c
    
    # Former firm names (Block 8) - if applicable
    # Employee disciplines (Block 9) - would need employee data
    # Experience profile (Block 10) - would need profile data
    
    return doc


def generate_full_sf330_word(proposal, selected_employees, selected_projects, matrix):
    """
    Generate complete SF330 as multiple Word documents or combined document
    Returns: dict with section names and document bytes
    """
    from models import Firm
    
    documents = {}
    
    # Get primary firm
    firm = proposal.firm
    
    # Section A/C - Contract Info and Team
    firms_data = [{'firm': firm, 'role': 'Prime', 'is_prime': True}] if firm else []
    doc_a = generate_section_a_c(proposal, firms_data)
    
    buffer = io.BytesIO()
    doc_a.save(buffer)
    documents['section_a_c'] = buffer.getvalue()
    
    # Section E - One per employee
    section_e_docs = []
    for emp_data in selected_employees:
        employee = emp_data.get('employee')
        experiences = emp_data.get('experiences', [])
        role = emp_data.get('role', '')
        
        if employee:
            employee.proposal_role = role
            doc_e = generate_section_e(employee, proposal, experiences)
            buffer = io.BytesIO()
            doc_e.save(buffer)
            section_e_docs.append({
                'name': employee.name,
                'data': buffer.getvalue()
            })
    documents['section_e'] = section_e_docs
    
    # Section F - One per project
    section_f_docs = []
    for idx, proj_data in enumerate(selected_projects):
        project = proj_data.get('project')
        if project:
            doc_f = generate_section_f(project, proposal, idx + 1)
            buffer = io.BytesIO()
            doc_f.save(buffer)
            section_f_docs.append({
                'name': project.title,
                'data': buffer.getvalue()
            })
    documents['section_f'] = section_f_docs
    
    # Section G - Matrix
    employees_with_roles = [
        {'employee': ed.get('employee'), 'role': ed.get('role', '')}
        for ed in selected_employees
    ]
    projects = [pd.get('project') for pd in selected_projects if pd.get('project')]
    
    doc_g = generate_section_g(employees_with_roles, projects, matrix)
    buffer = io.BytesIO()
    doc_g.save(buffer)
    documents['section_g'] = buffer.getvalue()
    
    # Section H - Additional Info
    doc_h = generate_section_h(proposal)
    buffer = io.BytesIO()
    doc_h.save(buffer)
    documents['section_h_i'] = buffer.getvalue()
    
    # Part II - Firm Qualifications
    if firm:
        doc_ii = generate_part_ii(firm)
        buffer = io.BytesIO()
        doc_ii.save(buffer)
        documents['part_ii'] = buffer.getvalue()
    
    return documents


def combine_documents_as_zip(documents):
    """
    Package multiple Word documents into a ZIP file
    Returns: bytes of ZIP archive
    """
    import zipfile
    
    buffer = io.BytesIO()
    
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        sections_order = ['section_a_c', 'section_e', 'section_f', 'section_g', 'section_h_i', 'part_ii']
        
        for section in sections_order:
            if section not in documents:
                continue
                
            data = documents[section]
            
            if isinstance(data, list):
                # Multiple docs (Section E, F)
                for idx, item in enumerate(data, 1):
                    name = item.get('name', f'item_{idx}')
                    # Sanitize filename
                    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
                    filename = f"{section}_{idx:02d}_{safe_name}.docx"
                    zf.writestr(filename, item['data'])
            else:
                # Single doc
                zf.writestr(f"{section}.docx", data)
    
    buffer.seek(0)
    return buffer.getvalue()


def generate_simple_sf330(proposal, employees_data, projects_data, firms_data, matrix_data):
    """
    Generate a simple Word document with all SF330 info (no template)
    Returns: bytes of the Word document
    """
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    
    doc = Document()
    
    # Set up styles
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(10)
    
    def add_heading(text, level=1):
        h = doc.add_heading(text, level=level)
        return h
    
    def add_field(label, value):
        p = doc.add_paragraph()
        p.add_run(f"{label}: ").bold = True
        p.add_run(str(value) if value else "")
        return p
    
    # Title
    title = doc.add_heading('SF330 - ARCHITECT-ENGINEER QUALIFICATIONS', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Part I - Contract-Specific Qualifications
    add_heading('PART I - CONTRACT-SPECIFIC QUALIFICATIONS', 1)
    
    # Section A - Contract Information
    add_heading('A. CONTRACT INFORMATION', 2)
    add_field('1. Title and Location', f"{proposal.contract_title or ''}, {proposal.contract_location or ''}")
    
    if proposal.public_notice_date:
        if hasattr(proposal.public_notice_date, 'strftime'):
            notice_date = proposal.public_notice_date.strftime('%m/%d/%Y')
        else:
            notice_date = str(proposal.public_notice_date)
    else:
        notice_date = ""
    add_field('2. Public Notice Date', notice_date)
    add_field('3. Solicitation or Project Number', proposal.solicitation_number or '')
    
    # Section B - Point of Contact
    add_heading('B. ARCHITECT-ENGINEER POINT OF CONTACT', 2)
    if proposal.firm:
        firm = proposal.firm
        poc_name = getattr(firm, 'point_of_contact_name', '') or ''
        poc_title = getattr(firm, 'point_of_contact_title', '') or ''
        add_field('4. Name and Title', f"{poc_name}, {poc_title}" if poc_title else poc_name)
        add_field('5. Name of Firm', firm.name or '')
        add_field('6. Telephone Number', getattr(firm, 'phone', '') or '')
        add_field('7. Fax Number', getattr(firm, 'fax', '') or '')
        add_field('8. E-mail Address', getattr(firm, 'email', '') or '')
    
    # Section C - Proposed Team
    add_heading('C. PROPOSED TEAM', 2)
    if firms_data:
        for idx, firm_info in enumerate(firms_data):
            firm = firm_info.get('firm')
            if firm:
                role = firm_info.get('role', '')
                loc = f"{firm.city}, {firm.state}" if firm.city else ""
                p = doc.add_paragraph()
                p.add_run(f"{chr(97+idx)}. ").bold = True
                p.add_run(f"{firm.name} - {loc}")
                if role:
                    p.add_run(f" ({role})")
    
    # Section D - Org Chart placeholder
    add_heading('D. ORGANIZATIONAL CHART OF PROPOSED TEAM', 2)
    doc.add_paragraph('(Attach organizational chart)')
    
    # Section E - Resumes
    add_heading('E. RESUMES OF KEY PERSONNEL PROPOSED FOR THIS CONTRACT', 2)
    
    for emp_data in employees_data:
        emp = emp_data.get('employee')
        if not emp:
            continue
        
        doc.add_paragraph()
        h = doc.add_heading(f"{emp.name}", 3)
        
        add_field('12. Name', emp.name)
        add_field('13. Role in This Contract', emp_data.get('role', '') or getattr(emp, 'role', ''))
        
        firm_name = ""
        if proposal.firm:
            firm_loc = f"{proposal.firm.city}, {proposal.firm.state}" if proposal.firm.city else ""
            firm_name = f"{proposal.firm.name}, {firm_loc}"
        add_field('14. Years Experience: a. Total', getattr(emp, 'years_experience_total', ''))
        add_field('14. Years Experience: b. With Current Firm', getattr(emp, 'years_experience_firm', ''))
        add_field('15. Firm Name and Location', firm_name)
        add_field('16. Education', getattr(emp, 'education', ''))
        add_field('17. Current Professional Registration', getattr(emp, 'registrations', ''))
        add_field('18. Other Professional Qualifications', getattr(emp, 'other_qualifications', ''))
        
        # Training
        if getattr(emp, 'training', ''):
            add_field('Training', emp.training)
        
        # Project Experience
        doc.add_paragraph()
        p = doc.add_paragraph()
        p.add_run('19. RELEVANT PROJECTS').bold = True
        
        experiences = emp_data.get('experiences', [])
        for exp_idx, exp in enumerate(experiences[:5]):
            exp_p = doc.add_paragraph()
            exp_p.add_run(f"({chr(97+exp_idx)}) ").bold = True
            title = getattr(exp, 'project_title', '') or getattr(exp, 'title', '') or ''
            location = getattr(exp, 'location', '') or ''
            year = getattr(exp, 'year_completed', '') or ''
            exp_p.add_run(f"{title}")
            if location:
                exp_p.add_run(f", {location}")
            if year:
                exp_p.add_run(f" ({year})")
            
            desc = getattr(exp, 'brief_description', '') or getattr(exp, 'description', '') or ''
            role = getattr(exp, 'role_performed', '') or getattr(exp, 'role', '') or ''
            if desc:
                doc.add_paragraph(desc)
            if role:
                add_field('Role', role)
        
        doc.add_page_break()
    
    # Section F - Example Projects
    add_heading('F. EXAMPLE PROJECTS WHICH BEST ILLUSTRATE PROPOSED TEAM\'S QUALIFICATIONS', 2)
    
    for idx, proj_data in enumerate(projects_data):
        proj = proj_data.get('project')
        if not proj:
            continue
        
        doc.add_paragraph()
        h = doc.add_heading(f"Project {idx + 1}: {proj.title}", 3)
        
        add_field('21. Title and Location', f"{proj.title}, {proj.location or ''}")
        year = getattr(proj, 'year_completed_professional', '') or ''
        add_field('22. Year Completed: Professional Services', year)
        year_const = getattr(proj, 'year_completed_construction', '') or ''
        if year_const:
            add_field('22. Year Completed: Construction', year_const)
        
        add_field('23a. Project Owner', getattr(proj, 'owner_name', '') or '')
        add_field('23b. Point of Contact Name', getattr(proj, 'owner_contact_name', '') or '')
        add_field('23c. Point of Contact Telephone', getattr(proj, 'owner_contact_phone', '') or '')
        
        # Get description (alternate or main)
        desc = proj_data.get('description') or getattr(proj, 'brief_description', '') or ''
        add_field('24. Brief Description', '')
        if desc:
            doc.add_paragraph(desc)
        
        # Firms involved
        if hasattr(proj, 'firm_involvements') and proj.firm_involvements:
            doc.add_paragraph()
            p = doc.add_paragraph()
            p.add_run('25. Firms Involved:').bold = True
            for fi in proj.firm_involvements:
                if fi.firm:
                    doc.add_paragraph(f"  - {fi.firm.name}: {fi.role or ''}")
        
        doc.add_page_break()
    
    # Section G - Key Personnel Participation Matrix
    add_heading('G. KEY PERSONNEL PARTICIPATION IN EXAMPLE PROJECTS', 2)
    
    if employees_data and projects_data:
        # Create table
        num_cols = min(len(projects_data), 10) + 2  # Name, Role, + projects
        table = doc.add_table(rows=1, cols=num_cols)
        table.style = 'Table Grid'
        
        # Header row
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Name'
        hdr_cells[1].text = 'Role'
        for idx, proj_data in enumerate(projects_data[:10]):
            proj = proj_data.get('project')
            if proj and idx + 2 < num_cols:
                hdr_cells[idx + 2].text = str(idx + 1)
        
        # Data rows
        for emp_data in employees_data:
            emp = emp_data.get('employee')
            if not emp:
                continue
            row = table.add_row().cells
            row[0].text = emp.name or ''
            row[1].text = emp_data.get('role', '') or ''
            
            # Check matrix for participation
            for proj_idx, proj_data in enumerate(projects_data[:10]):
                proj = proj_data.get('project')
                if proj and proj_idx + 2 < num_cols:
                    # Check if employee participated in this project
                    key = (emp.id, proj.id)
                    if matrix_data and key in matrix_data:
                        row[proj_idx + 2].text = 'X'
    
    doc.add_page_break()
    
    # Section H - Additional Information
    add_heading('H. ADDITIONAL INFORMATION', 2)
    if proposal.section_h_narrative:
        doc.add_paragraph(proposal.section_h_narrative)
    else:
        doc.add_paragraph('(No additional information provided)')
    
    # Section I - Authorized Representative
    add_heading('I. AUTHORIZED REPRESENTATIVE', 2)
    if proposal.firm:
        poc_name = getattr(proposal.firm, 'point_of_contact_name', '') or ''
        poc_title = getattr(proposal.firm, 'point_of_contact_title', '') or ''
        add_field('Signature of Authorized Representative', '')
        add_field('Name', poc_name)
        add_field('Title', poc_title)
        from datetime import datetime
        add_field('Date', datetime.now().strftime('%m/%d/%Y'))
    
    doc.add_page_break()
    
    # Part II - General Qualifications
    add_heading('PART II - GENERAL QUALIFICATIONS', 1)
    
    if proposal.firm:
        firm = proposal.firm
        add_field('2a. Firm Name', firm.name or '')
        add_field('2b. Street Address', getattr(firm, 'street_address', '') or '')
        add_field('2c. City', getattr(firm, 'city', '') or '')
        add_field('2d. State', getattr(firm, 'state', '') or '')
        add_field('2e. Zip Code', getattr(firm, 'zip_code', '') or '')
        add_field('3. Year Established', getattr(firm, 'year_established', '') or '')
        add_field('4. UEI Number', getattr(firm, 'uei', '') or '')
        add_field('5a. Ownership Type', getattr(firm, 'ownership_type', '') or '')
        
        poc_name = getattr(firm, 'point_of_contact_name', '') or ''
        poc_title = getattr(firm, 'point_of_contact_title', '') or ''
        add_field('6a. Point of Contact Name and Title', f"{poc_name}, {poc_title}" if poc_title else poc_name)
        add_field('6b. Telephone Number', getattr(firm, 'phone', '') or '')
        add_field('6c. E-mail Address', getattr(firm, 'email', '') or '')
    
    # Save to buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
