import os
import json
from flask import render_template, request, jsonify, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from main import app
from database import db
from models import (
    Firm, Employee, Project, EmployeeProjectLink, Proposal,
    ProposalSelectedEmployee, ProposalSelectedProject, ProposalEmployeeRelevantProject,
    ProjectFirmInvolvement
)
from document_parser import extract_text_from_file
from gemini_service import detect_document_type, parse_employee_resume, parse_project_sheet, parse_firm_info
from pdf_generator import generate_full_sf330, get_form_fields
import io

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'xlsx', 'xls', 'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    proposals = Proposal.query.order_by(Proposal.updated_at.desc()).limit(5).all()
    employees_count = Employee.query.count()
    projects_count = Project.query.count()
    firms_count = Firm.query.count()
    return render_template('index.html', 
                         proposals=proposals,
                         employees_count=employees_count,
                         projects_count=projects_count,
                         firms_count=firms_count)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Supported: PDF, DOCX, XLSX, TXT'}), 400
    
    try:
        file_content = file.read()
        text = extract_text_from_file(file.filename, file_content)
        
        doc_type = detect_document_type(text)
        
        parsed_data = {}
        if doc_type == 'employee':
            parsed_data = parse_employee_resume(text)
        elif doc_type == 'project':
            parsed_data = parse_project_sheet(text)
        elif doc_type == 'firm':
            parsed_data = parse_firm_info(text)
        else:
            return jsonify({
                'doc_type': 'unknown',
                'raw_text': text[:5000],
                'message': 'Could not determine document type. Please specify manually.'
            })
        
        return jsonify({
            'doc_type': doc_type,
            'parsed_data': parsed_data,
            'raw_text': text[:2000]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/save-parsed-data', methods=['POST'])
def save_parsed_data():
    data = request.json
    doc_type = data.get('doc_type')
    parsed_data = data.get('parsed_data')
    
    try:
        if doc_type == 'employee':
            employee = Employee(
                name=parsed_data.get('name', 'Unknown'),
                title=parsed_data.get('title'),
                role=parsed_data.get('role'),
                years_experience_total=parsed_data.get('years_experience_total'),
                years_experience_firm=parsed_data.get('years_experience_firm'),
                education=parsed_data.get('education'),
                registrations=parsed_data.get('registrations'),
                training=parsed_data.get('training'),
                other_qualifications=parsed_data.get('other_qualifications')
            )
            db.session.add(employee)
            db.session.commit()
            return jsonify({'success': True, 'id': employee.id, 'message': 'Employee saved successfully'})
        
        elif doc_type == 'project':
            project = Project(
                title=parsed_data.get('title', 'Untitled Project'),
                location=parsed_data.get('location'),
                year_completed_professional=parsed_data.get('year_completed_professional'),
                year_completed_construction=parsed_data.get('year_completed_construction'),
                owner_name=parsed_data.get('owner_name'),
                owner_contact_name=parsed_data.get('owner_contact_name'),
                owner_contact_phone=parsed_data.get('owner_contact_phone'),
                project_cost=parsed_data.get('project_cost'),
                project_delivery_method=parsed_data.get('project_delivery_method'),
                brief_description=parsed_data.get('brief_description'),
                relevance_writeup=parsed_data.get('relevance_writeup')
            )
            db.session.add(project)
            db.session.commit()
            
            team_members = parsed_data.get('team_members', [])
            for member in team_members:
                employee = Employee.query.filter_by(name=member.get('name')).first()
                if employee:
                    link = EmployeeProjectLink(
                        employee_id=employee.id,
                        project_id=project.id,
                        role_on_project=member.get('role_on_project')
                    )
                    db.session.add(link)
            
            db.session.commit()
            return jsonify({'success': True, 'id': project.id, 'message': 'Project saved successfully'})
        
        elif doc_type == 'firm':
            firm = Firm(
                name=parsed_data.get('name', 'Unknown Firm'),
                uei=parsed_data.get('uei'),
                street_address=parsed_data.get('street_address'),
                city=parsed_data.get('city'),
                state=parsed_data.get('state'),
                zip_code=parsed_data.get('zip_code'),
                country=parsed_data.get('country', 'USA'),
                year_established=parsed_data.get('year_established'),
                ownership_type=parsed_data.get('ownership_type'),
                is_small_business=parsed_data.get('is_small_business', False),
                small_business_categories=parsed_data.get('small_business_categories'),
                phone=parsed_data.get('phone'),
                fax=parsed_data.get('fax'),
                email=parsed_data.get('email'),
                point_of_contact_name=parsed_data.get('point_of_contact_name'),
                point_of_contact_title=parsed_data.get('point_of_contact_title')
            )
            db.session.add(firm)
            db.session.commit()
            return jsonify({'success': True, 'id': firm.id, 'message': 'Firm saved successfully'})
        
        else:
            return jsonify({'error': 'Invalid document type'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/employees')
def employees():
    employees = Employee.query.order_by(Employee.name).all()
    return render_template('employees.html', employees=employees)


@app.route('/employees/add', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        data = request.form
        employee = Employee(
            name=data.get('name', ''),
            title=data.get('title'),
            role=data.get('role'),
            years_experience_total=int(data.get('years_experience_total') or 0) if data.get('years_experience_total') else None,
            years_experience_firm=int(data.get('years_experience_firm') or 0) if data.get('years_experience_firm') else None,
            education=data.get('education'),
            registrations=data.get('registrations'),
            training=data.get('training'),
            other_qualifications=data.get('other_qualifications'),
            firm_id=int(data.get('firm_id')) if data.get('firm_id') else None
        )
        db.session.add(employee)
        db.session.commit()
        return redirect(f'/employees/{employee.id}')
    
    firms = Firm.query.all()
    return render_template('employee_add.html', firms=firms)


@app.route('/employees/<int:id>')
def employee_detail(id):
    employee = Employee.query.get_or_404(id)
    projects = Project.query.join(EmployeeProjectLink).filter(EmployeeProjectLink.employee_id == id).all()
    firms = Firm.query.all()
    return render_template('employee_detail.html', employee=employee, projects=projects, firms=firms)


@app.route('/employees/<int:id>', methods=['PUT'])
def update_employee(id):
    employee = Employee.query.get_or_404(id)
    data = request.json
    
    employee.name = data.get('name', employee.name)
    employee.title = data.get('title', employee.title)
    employee.role = data.get('role', employee.role)
    employee.years_experience_total = data.get('years_experience_total', employee.years_experience_total)
    employee.years_experience_firm = data.get('years_experience_firm', employee.years_experience_firm)
    employee.education = data.get('education', employee.education)
    employee.registrations = data.get('registrations', employee.registrations)
    employee.training = data.get('training', employee.training)
    employee.other_qualifications = data.get('other_qualifications', employee.other_qualifications)
    employee.firm_id = data.get('firm_id', employee.firm_id)
    
    db.session.commit()
    return jsonify({'success': True})


@app.route('/projects')
def projects():
    projects = Project.query.order_by(Project.title).all()
    return render_template('projects.html', projects=projects)


@app.route('/projects/add', methods=['GET', 'POST'])
def add_project():
    if request.method == 'POST':
        data = request.form
        project = Project(
            title=data.get('title', ''),
            location=data.get('location'),
            year_completed_professional=data.get('year_completed_professional'),
            year_completed_construction=data.get('year_completed_construction'),
            owner_name=data.get('owner_name'),
            owner_contact_name=data.get('owner_contact_name'),
            owner_contact_phone=data.get('owner_contact_phone'),
            project_cost=data.get('project_cost'),
            project_delivery_method=data.get('project_delivery_method'),
            brief_description=data.get('brief_description'),
            relevance_writeup=data.get('relevance_writeup')
        )
        db.session.add(project)
        db.session.commit()
        return redirect(f'/projects/{project.id}')
    
    return render_template('project_add.html')


@app.route('/projects/<int:id>')
def project_detail(id):
    project = Project.query.get_or_404(id)
    employees = Employee.query.join(EmployeeProjectLink).filter(EmployeeProjectLink.project_id == id).all()
    all_employees = Employee.query.all()
    return render_template('project_detail.html', project=project, employees=employees, all_employees=all_employees)


@app.route('/projects/<int:id>', methods=['PUT'])
def update_project(id):
    project = Project.query.get_or_404(id)
    data = request.json
    
    project.title = data.get('title', project.title)
    project.location = data.get('location', project.location)
    project.year_completed_professional = data.get('year_completed_professional', project.year_completed_professional)
    project.year_completed_construction = data.get('year_completed_construction', project.year_completed_construction)
    project.owner_name = data.get('owner_name', project.owner_name)
    project.owner_contact_name = data.get('owner_contact_name', project.owner_contact_name)
    project.owner_contact_phone = data.get('owner_contact_phone', project.owner_contact_phone)
    project.project_cost = data.get('project_cost', project.project_cost)
    project.brief_description = data.get('brief_description', project.brief_description)
    project.relevance_writeup = data.get('relevance_writeup', project.relevance_writeup)
    
    db.session.commit()
    return jsonify({'success': True})


@app.route('/projects/<int:project_id>/link-employee', methods=['POST'])
def link_employee_to_project(project_id):
    data = request.json
    employee_id = data.get('employee_id')
    role = data.get('role')
    
    existing = EmployeeProjectLink.query.filter_by(
        employee_id=employee_id, 
        project_id=project_id
    ).first()
    
    if existing:
        existing.role_on_project = role
    else:
        link = EmployeeProjectLink(
            employee_id=employee_id,
            project_id=project_id,
            role_on_project=role
        )
        db.session.add(link)
    
    db.session.commit()
    return jsonify({'success': True})


@app.route('/firms')
def firms():
    firms = Firm.query.order_by(Firm.name).all()
    return render_template('firms.html', firms=firms)


@app.route('/firms/add', methods=['GET', 'POST'])
def add_firm():
    if request.method == 'POST':
        data = request.form
        firm = Firm(
            name=data.get('name', ''),
            uei=data.get('uei'),
            street_address=data.get('street_address'),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zip_code'),
            country=data.get('country', 'USA'),
            year_established=int(data.get('year_established')) if data.get('year_established') else None,
            ownership_type=data.get('ownership_type'),
            is_small_business=data.get('is_small_business') == 'on',
            small_business_categories=data.get('small_business_categories'),
            phone=data.get('phone'),
            fax=data.get('fax'),
            email=data.get('email'),
            point_of_contact_name=data.get('point_of_contact_name'),
            point_of_contact_title=data.get('point_of_contact_title')
        )
        db.session.add(firm)
        db.session.commit()
        return redirect(f'/firms/{firm.id}')
    
    return render_template('firm_add.html')


@app.route('/firms/<int:id>')
def firm_detail(id):
    firm = Firm.query.get_or_404(id)
    return render_template('firm_detail.html', firm=firm)


@app.route('/proposals')
def proposals():
    proposals = Proposal.query.order_by(Proposal.updated_at.desc()).all()
    return render_template('proposals.html', proposals=proposals)


@app.route('/proposals/new', methods=['GET', 'POST'])
def new_proposal():
    if request.method == 'GET':
        firms = Firm.query.all()
        return render_template('proposal_wizard_step1.html', firms=firms)
    
    data = request.form
    proposal = Proposal(
        name=data.get('name'),
        contract_title=data.get('contract_title'),
        contract_location=data.get('contract_location'),
        public_notice_date=data.get('public_notice_date'),
        solicitation_number=data.get('solicitation_number'),
        firm_id=data.get('firm_id') if data.get('firm_id') else None
    )
    db.session.add(proposal)
    db.session.commit()
    
    return redirect(url_for('proposal_step2', id=proposal.id))


@app.route('/proposals/<int:id>/step2', methods=['GET', 'POST'])
def proposal_step2(id):
    proposal = Proposal.query.get_or_404(id)
    
    if request.method == 'GET':
        employees = Employee.query.order_by(Employee.name).all()
        selected_ids = [se.employee_id for se in proposal.selected_employees]
        return render_template('proposal_wizard_step2.html', 
                             proposal=proposal, 
                             employees=employees,
                             selected_ids=selected_ids)
    
    data = request.json
    employee_ids = data.get('employee_ids', [])
    roles = data.get('roles', {})
    
    ProposalSelectedEmployee.query.filter_by(proposal_id=id).delete()
    
    for idx, emp_id in enumerate(employee_ids):
        pse = ProposalSelectedEmployee(
            proposal_id=id,
            employee_id=emp_id,
            role_in_contract=roles.get(str(emp_id), ''),
            display_order=idx
        )
        db.session.add(pse)
    
    db.session.commit()
    return jsonify({'success': True, 'redirect': url_for('proposal_step3', id=id)})


@app.route('/proposals/<int:id>/step3', methods=['GET', 'POST'])
def proposal_step3(id):
    proposal = Proposal.query.get_or_404(id)
    
    if request.method == 'GET':
        projects = Project.query.order_by(Project.title).all()
        selected_ids = [sp.project_id for sp in proposal.selected_projects]
        return render_template('proposal_wizard_step3.html', 
                             proposal=proposal, 
                             projects=projects,
                             selected_ids=selected_ids)
    
    data = request.json
    project_ids = data.get('project_ids', [])
    writeups = data.get('writeups', {})
    
    ProposalSelectedProject.query.filter_by(proposal_id=id).delete()
    
    for idx, proj_id in enumerate(project_ids[:10]):
        psp = ProposalSelectedProject(
            proposal_id=id,
            project_id=proj_id,
            display_order=idx,
            custom_writeup=writeups.get(str(proj_id), '')
        )
        db.session.add(psp)
    
    db.session.commit()
    return jsonify({'success': True, 'redirect': url_for('proposal_step4', id=id)})


@app.route('/proposals/<int:id>/step4')
def proposal_step4(id):
    proposal = Proposal.query.get_or_404(id)
    
    selected_employees = ProposalSelectedEmployee.query.filter_by(proposal_id=id)\
        .order_by(ProposalSelectedEmployee.display_order).all()
    selected_projects = ProposalSelectedProject.query.filter_by(proposal_id=id)\
        .order_by(ProposalSelectedProject.display_order).all()
    
    matrix = {}
    for pse in selected_employees:
        matrix[pse.employee_id] = {}
        for psp in selected_projects:
            link = EmployeeProjectLink.query.filter_by(
                employee_id=pse.employee_id,
                project_id=psp.project_id
            ).first()
            matrix[pse.employee_id][psp.project_id] = link is not None
    
    return render_template('proposal_wizard_step4.html',
                         proposal=proposal,
                         selected_employees=selected_employees,
                         selected_projects=selected_projects,
                         matrix=matrix)


@app.route('/proposals/<int:id>/employee/<int:emp_id>/relevant-projects', methods=['GET', 'POST'])
def employee_relevant_projects(id, emp_id):
    proposal = Proposal.query.get_or_404(id)
    pse = ProposalSelectedEmployee.query.filter_by(proposal_id=id, employee_id=emp_id).first_or_404()
    
    if request.method == 'GET':
        all_projects = Project.query.order_by(Project.title).all()
        selected_ids = [rp.project_id for rp in pse.relevant_projects]
        employee = Employee.query.get(emp_id)
        return render_template('employee_relevant_projects.html',
                             proposal=proposal,
                             employee=employee,
                             projects=all_projects,
                             selected_ids=selected_ids)
    
    data = request.json
    project_ids = data.get('project_ids', [])[:5]
    
    ProposalEmployeeRelevantProject.query.filter_by(proposal_selected_employee_id=pse.id).delete()
    
    for idx, proj_id in enumerate(project_ids):
        perp = ProposalEmployeeRelevantProject(
            proposal_selected_employee_id=pse.id,
            project_id=proj_id,
            display_order=idx
        )
        db.session.add(perp)
    
    db.session.commit()
    return jsonify({'success': True})


@app.route('/proposals/<int:id>/generate-pdf')
def generate_proposal_pdf(id):
    proposal = Proposal.query.get_or_404(id)
    
    selected_employees = ProposalSelectedEmployee.query.filter_by(proposal_id=id)\
        .order_by(ProposalSelectedEmployee.display_order).all()
    selected_projects = ProposalSelectedProject.query.filter_by(proposal_id=id)\
        .order_by(ProposalSelectedProject.display_order).all()
    
    employee_project_matrix = {}
    for pse in selected_employees:
        employee_project_matrix[pse.employee_id] = set()
        for psp in selected_projects:
            link = EmployeeProjectLink.query.filter_by(
                employee_id=pse.employee_id,
                project_id=psp.project_id
            ).first()
            if link:
                employee_project_matrix[pse.employee_id].add(psp.project_id)
    
    proposal_data = {
        'contract_title': proposal.contract_title,
        'contract_location': proposal.contract_location,
        'public_notice_date': proposal.public_notice_date,
        'solicitation_number': proposal.solicitation_number,
        'firm': {
            'name': proposal.firm.name if proposal.firm else '',
            'street_address': proposal.firm.street_address if proposal.firm else '',
            'city': proposal.firm.city if proposal.firm else '',
            'state': proposal.firm.state if proposal.firm else '',
            'zip_code': proposal.firm.zip_code if proposal.firm else '',
            'year_established': proposal.firm.year_established if proposal.firm else '',
            'uei': proposal.firm.uei if proposal.firm else '',
            'ownership_type': proposal.firm.ownership_type if proposal.firm else '',
            'point_of_contact_name': proposal.firm.point_of_contact_name if proposal.firm else '',
            'phone': proposal.firm.phone if proposal.firm else '',
            'email': proposal.firm.email if proposal.firm else '',
        } if proposal.firm else {},
        'employees': [{
            'id': pse.employee_id,
            'name': pse.employee.name,
            'role_in_contract': pse.role_in_contract or pse.employee.role,
            'years_experience_total': pse.employee.years_experience_total,
            'years_experience_firm': pse.employee.years_experience_firm,
            'firm_name': pse.employee.firm.name if pse.employee.firm else '',
            'education': pse.employee.education,
            'registrations': pse.employee.registrations,
            'training': pse.employee.training,
            'other_qualifications': pse.employee.other_qualifications,
        } for pse in selected_employees],
        'projects': [{
            'id': psp.project_id,
            'title': psp.project.title,
            'location': psp.project.location,
            'year_completed_professional': psp.project.year_completed_professional,
            'year_completed_construction': psp.project.year_completed_construction,
            'owner_name': psp.project.owner_name,
            'owner_contact_name': psp.project.owner_contact_name,
            'owner_contact_phone': psp.project.owner_contact_phone,
            'brief_description': psp.project.brief_description,
            'custom_writeup': psp.custom_writeup or psp.project.relevance_writeup or '',
        } for psp in selected_projects],
        'employee_project_matrix': employee_project_matrix
    }
    
    try:
        pdf_bytes = generate_full_sf330(proposal_data)
        
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"SF330_{proposal.name.replace(' ', '_')}.pdf"
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('proposal_step4', id=id))


@app.route('/proposals/<int:id>/finalize', methods=['POST'])
def finalize_proposal(id):
    proposal = Proposal.query.get_or_404(id)
    proposal.status = 'finalized'
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/employees')
def api_employees():
    employees = Employee.query.order_by(Employee.name).all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'title': e.title,
        'role': e.role
    } for e in employees])


@app.route('/api/projects')
def api_projects():
    projects = Project.query.order_by(Project.title).all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'location': p.location,
        'owner_name': p.owner_name
    } for p in projects])


@app.route('/api/firms')
def api_firms():
    firms = Firm.query.order_by(Firm.name).all()
    return jsonify([{
        'id': f.id,
        'name': f.name,
        'city': f.city,
        'state': f.state
    } for f in firms])
