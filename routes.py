import os
import json
from flask import render_template, request, jsonify, redirect, url_for, flash, send_file, session
from werkzeug.utils import secure_filename
from main import app
from database import db
from models import (
    Firm, Employee, Project, EmployeeProjectLink, Proposal,
    ProposalSelectedEmployee, ProposalSelectedProject, ProposalEmployeeRelevantProject,
    ProjectFirmInvolvement, EmployeeProjectExperience, ProjectAlternateDescription
)
from document_parser import extract_text_from_file
from gemini_service import detect_document_type, parse_employee_resume, parse_project_sheet, parse_firm_info, find_matching_employee, combine_and_rewrite_text
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
    force_new = data.get('force_new', False)
    
    try:
        if doc_type == 'employee':
            name = parsed_data.get('name', 'Unknown')
            
            if not force_new:
                existing_id = find_matching_employee(name)
                if existing_id:
                    session['pending_employee_data'] = parsed_data
                    return jsonify({
                        'success': False, 
                        'duplicate_found': True,
                        'existing_id': existing_id,
                        'message': f'An employee named "{name}" already exists. Review and merge the data.'
                    })
            
            employee = Employee(
                name=name,
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
            
            project_experiences = parsed_data.get('project_experience', [])
            if project_experiences:
                for proj in project_experiences:
                    if proj.get('project_title'):
                        exp = EmployeeProjectExperience(
                            employee_id=employee.id,
                            project_title=proj.get('project_title'),
                            location=proj.get('location'),
                            owner_name=proj.get('owner_name'),
                            project_cost=proj.get('project_cost'),
                            year_completed=proj.get('year_completed'),
                            role_performed=proj.get('role_performed'),
                            brief_description=proj.get('brief_description'),
                            firm_name=proj.get('firm_name'),
                            is_current_firm=False
                        )
                        db.session.add(exp)
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
    project_experiences = EmployeeProjectExperience.query.filter_by(employee_id=id).order_by(EmployeeProjectExperience.year_completed.desc()).all()
    firms = Firm.query.all()
    return render_template('employee_detail.html', employee=employee, projects=projects, project_experiences=project_experiences, firms=firms)


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


@app.route('/employees/<int:id>/project-experience', methods=['POST'])
def add_project_experience(id):
    employee = Employee.query.get_or_404(id)
    data = request.json
    
    exp = EmployeeProjectExperience(
        employee_id=employee.id,
        project_title=data.get('project_title', ''),
        location=data.get('location'),
        owner_name=data.get('owner_name'),
        project_cost=data.get('project_cost'),
        year_completed=data.get('year_completed'),
        role_performed=data.get('role_performed'),
        brief_description=data.get('brief_description'),
        firm_name=data.get('firm_name'),
        is_current_firm=data.get('is_current_firm', False)
    )
    db.session.add(exp)
    db.session.commit()
    return jsonify({'success': True, 'id': exp.id})


@app.route('/employees/<int:id>/project-experience/<int:exp_id>', methods=['PUT'])
def update_project_experience(id, exp_id):
    exp = EmployeeProjectExperience.query.filter_by(id=exp_id, employee_id=id).first_or_404()
    data = request.json
    
    exp.project_title = data.get('project_title', exp.project_title)
    exp.location = data.get('location', exp.location)
    exp.owner_name = data.get('owner_name', exp.owner_name)
    exp.project_cost = data.get('project_cost', exp.project_cost)
    exp.year_completed = data.get('year_completed', exp.year_completed)
    exp.role_performed = data.get('role_performed', exp.role_performed)
    exp.brief_description = data.get('brief_description', exp.brief_description)
    exp.firm_name = data.get('firm_name', exp.firm_name)
    exp.is_current_firm = data.get('is_current_firm', exp.is_current_firm)
    
    db.session.commit()
    return jsonify({'success': True})


@app.route('/employees/<int:id>/project-experience/<int:exp_id>', methods=['DELETE'])
def delete_project_experience(id, exp_id):
    exp = EmployeeProjectExperience.query.filter_by(id=exp_id, employee_id=id).first_or_404()
    db.session.delete(exp)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/employees/<int:id>', methods=['DELETE'])
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    EmployeeProjectExperience.query.filter_by(employee_id=id).delete()
    EmployeeProjectLink.query.filter_by(employee_id=id).delete()
    ProposalSelectedEmployee.query.filter_by(employee_id=id).delete()
    db.session.delete(employee)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/employees/merge-duplicates')
def merge_employees_page():
    ids = request.args.get('ids', '')
    id_list = [int(x) for x in ids.split(',') if x.isdigit()]
    if len(id_list) < 2:
        return redirect('/employees')
    
    employees = Employee.query.filter(Employee.id.in_(id_list)).all()
    if len(employees) < 2:
        return redirect('/employees')
    
    employees_data = [{
        'id': e.id,
        'name': e.name,
        'title': e.title,
        'role': e.role,
        'years_experience_firm': e.years_experience_firm,
        'years_experience_total': e.years_experience_total,
        'education': e.education,
        'registrations': e.registrations,
        'training': e.training,
        'other_qualifications': e.other_qualifications
    } for e in employees]
    
    return render_template('employee_merge_duplicates.html', employees=employees, employees_json=employees_data)


@app.route('/employees/merge-duplicates', methods=['POST'])
def merge_employees():
    data = request.json
    primary_id = data.get('primary_id')
    merge_ids = data.get('merge_ids', [])
    merged_data = data.get('merged_data', {})
    
    primary = Employee.query.get_or_404(primary_id)
    
    for key, value in merged_data.items():
        if hasattr(primary, key):
            setattr(primary, key, value)
    
    for merge_id in merge_ids:
        if merge_id == primary_id:
            continue
        merge_emp = Employee.query.get(merge_id)
        if not merge_emp:
            continue
        
        for link in EmployeeProjectLink.query.filter_by(employee_id=merge_id).all():
            existing = EmployeeProjectLink.query.filter_by(
                employee_id=primary_id, project_id=link.project_id
            ).first()
            if not existing:
                link.employee_id = primary_id
            else:
                db.session.delete(link)
        
        for exp in merge_emp.project_experiences:
            existing = EmployeeProjectExperience.query.filter_by(
                employee_id=primary_id,
                project_title=exp.project_title,
                owner_name=exp.owner_name,
                firm_name=exp.firm_name
            ).first()
            if not existing:
                exp.employee_id = primary_id
            else:
                db.session.delete(exp)
        
        ProposalSelectedEmployee.query.filter_by(employee_id=merge_id).delete()
        db.session.delete(merge_emp)
    
    db.session.commit()
    return jsonify({'success': True, 'redirect': f'/employees/{primary_id}'})


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


@app.route('/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    project = Project.query.get_or_404(id)
    EmployeeProjectLink.query.filter_by(project_id=id).delete()
    ProposalEmployeeRelevantProject.query.filter_by(project_id=id).delete()
    ProposalSelectedProject.query.filter_by(project_id=id).delete()
    db.session.delete(project)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/projects/merge-duplicates')
def merge_projects_page():
    ids = request.args.get('ids', '')
    id_list = [int(x) for x in ids.split(',') if x.isdigit()]
    if len(id_list) < 2:
        return redirect('/projects')
    
    projects = Project.query.filter(Project.id.in_(id_list)).all()
    if len(projects) < 2:
        return redirect('/projects')
    
    projects_data = [{
        'id': p.id,
        'title': p.title,
        'location': p.location,
        'year_completed_professional': p.year_completed_professional,
        'year_completed_construction': p.year_completed_construction,
        'owner_name': p.owner_name,
        'owner_contact_name': p.owner_contact_name,
        'owner_contact_phone': p.owner_contact_phone,
        'project_cost': p.project_cost,
        'project_delivery_method': p.project_delivery_method,
        'brief_description': p.brief_description,
        'relevance_writeup': p.relevance_writeup
    } for p in projects]
    
    return render_template('project_merge_duplicates.html', projects=projects, projects_json=projects_data)


@app.route('/projects/merge-duplicates', methods=['POST'])
def merge_projects():
    data = request.json
    primary_id = data.get('primary_id')
    merge_ids = data.get('merge_ids', [])
    merged_data = data.get('merged_data', {})
    
    primary = Project.query.get_or_404(primary_id)
    
    for key, value in merged_data.items():
        if hasattr(primary, key):
            setattr(primary, key, value)
    
    for merge_id in merge_ids:
        if merge_id == primary_id:
            continue
        merge_proj = Project.query.get(merge_id)
        if not merge_proj:
            continue
        
        for link in EmployeeProjectLink.query.filter_by(project_id=merge_id).all():
            existing = EmployeeProjectLink.query.filter_by(
                employee_id=link.employee_id, project_id=primary_id
            ).first()
            if not existing:
                link.project_id = primary_id
            else:
                db.session.delete(link)
        
        ProposalEmployeeRelevantProject.query.filter_by(project_id=merge_id).update({'project_id': primary_id})
        ProposalSelectedProject.query.filter_by(project_id=merge_id).delete()
        db.session.delete(merge_proj)
    
    db.session.commit()
    return jsonify({'success': True, 'redirect': f'/projects/{primary_id}'})


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


@app.route('/projects/<int:project_id>/alternate-descriptions', methods=['POST'])
def add_alternate_description(project_id):
    data = request.json
    alt_desc = ProjectAlternateDescription(
        project_id=project_id,
        label=data.get('label', 'Alternate'),
        description=data.get('description', '')
    )
    db.session.add(alt_desc)
    db.session.commit()
    return jsonify({'success': True, 'id': alt_desc.id})


@app.route('/projects/<int:project_id>/alternate-descriptions/<int:alt_id>', methods=['PUT'])
def update_alternate_description(project_id, alt_id):
    alt_desc = ProjectAlternateDescription.query.filter_by(id=alt_id, project_id=project_id).first_or_404()
    data = request.json
    alt_desc.label = data.get('label', alt_desc.label)
    alt_desc.description = data.get('description', alt_desc.description)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/projects/<int:project_id>/alternate-descriptions/<int:alt_id>', methods=['DELETE'])
def delete_alternate_description(project_id, alt_id):
    alt_desc = ProjectAlternateDescription.query.filter_by(id=alt_id, project_id=project_id).first_or_404()
    db.session.delete(alt_desc)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/rewrite-description', methods=['POST'])
def rewrite_description():
    data = request.json
    description = data.get('description', '')
    
    if not description:
        return jsonify({'success': False, 'error': 'No description provided'})
    
    prompt = f"""You are a senior structural engineer with extensive experience in bridge inspection and rehabilitation.
Rewrite the following project description in a professional, technical tone appropriate for a federal SF330 proposal.
Focus on structural engineering aspects, bridge inspection methodologies, load ratings, condition assessments, and any rehabilitation or repair work.
Keep the same factual content but enhance the language to demonstrate technical expertise.
Keep the description concise (under 300 words) and suitable for Block 24 of SF330 Section F.

Original description:
{description}

Rewritten description (return ONLY the rewritten text, no explanations):"""
    
    try:
        from gemini_service import client
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        rewritten = response.text.strip()
        return jsonify({'success': True, 'rewritten': rewritten})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


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


@app.route('/proposals/parse-rfp', methods=['POST'])
def parse_rfp():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        from document_parser import extract_text_from_file
        from gemini_service import parse_rfp_rfq
        
        text = extract_text_from_file(file)
        if not text:
            return jsonify({'error': 'Could not extract text from file'}), 400
        
        parsed_data = parse_rfp_rfq(text)
        return jsonify({'success': True, 'data': parsed_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
        selected_alt_descs = {sp.project_id: sp.alternate_description_id for sp in proposal.selected_projects if sp.alternate_description_id}
        return render_template('proposal_wizard_step3.html', 
                             proposal=proposal, 
                             projects=projects,
                             selected_ids=selected_ids,
                             selected_alt_descs=selected_alt_descs)
    
    data = request.json
    project_ids = data.get('project_ids', [])
    writeups = data.get('writeups', {})
    desc_versions = data.get('desc_versions', {})
    
    ProposalSelectedProject.query.filter_by(proposal_id=id).delete()
    
    for idx, proj_id in enumerate(project_ids[:10]):
        alt_desc_id = desc_versions.get(str(proj_id))
        if alt_desc_id:
            alt_desc = ProjectAlternateDescription.query.filter_by(id=alt_desc_id, project_id=proj_id).first()
            alt_desc_id = alt_desc.id if alt_desc else None
        psp = ProposalSelectedProject(
            proposal_id=id,
            project_id=proj_id,
            display_order=idx,
            custom_writeup=writeups.get(str(proj_id), ''),
            alternate_description_id=alt_desc_id
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
            'project_experiences': [{
                'project_title': exp.project_title,
                'location': exp.location,
                'owner_name': exp.owner_name,
                'project_cost': exp.project_cost,
                'year_completed': exp.year_completed,
                'role_performed': exp.role_performed,
                'brief_description': exp.brief_description,
                'firm_name': exp.firm_name,
            } for exp in pse.employee.project_experiences],
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
            'brief_description': psp.alternate_description.description if psp.alternate_description else psp.project.brief_description,
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


@app.route('/employees/compare/<int:existing_id>')
def employee_compare(existing_id):
    existing = Employee.query.get_or_404(existing_id)
    
    parsed_new = session.get('pending_employee_data', {})
    
    if not parsed_new:
        new_data = request.args.get('new_data')
        if new_data:
            try:
                parsed_new = json.loads(new_data)
            except:
                parsed_new = {}
    
    existing_experiences = EmployeeProjectExperience.query.filter_by(employee_id=existing_id).all()
    
    existing_data = {
        'name': existing.name,
        'title': existing.title,
        'role': existing.role,
        'years_experience_total': existing.years_experience_total,
        'years_experience_firm': existing.years_experience_firm,
        'education': existing.education,
        'registrations': existing.registrations,
        'training': existing.training,
        'other_qualifications': existing.other_qualifications,
        'project_experience': [{
            'project_title': exp.project_title,
            'location': exp.location,
            'owner_name': exp.owner_name,
            'project_cost': exp.project_cost,
            'year_completed': exp.year_completed,
            'role_performed': exp.role_performed,
            'brief_description': exp.brief_description,
            'firm_name': exp.firm_name
        } for exp in existing_experiences]
    }
    
    return render_template('employee_compare.html', 
                          existing=existing,
                          existing_data=existing_data,
                          new_data=parsed_new)


@app.route('/employees/merge/<int:existing_id>', methods=['POST'])
def employee_merge(existing_id):
    existing = Employee.query.get_or_404(existing_id)
    data = request.json
    merged_data = data.get('merged_data', {})
    new_project_experiences = data.get('new_project_experiences', [])
    
    try:
        if merged_data.get('name'):
            existing.name = merged_data['name']
        if merged_data.get('title'):
            existing.title = merged_data['title']
        if merged_data.get('role'):
            existing.role = merged_data['role']
        if merged_data.get('years_experience_total') is not None:
            existing.years_experience_total = merged_data['years_experience_total']
        if merged_data.get('years_experience_firm') is not None:
            existing.years_experience_firm = merged_data['years_experience_firm']
        if merged_data.get('education'):
            existing.education = merged_data['education']
        if merged_data.get('registrations'):
            existing.registrations = merged_data['registrations']
        if merged_data.get('training'):
            existing.training = merged_data['training']
        if merged_data.get('other_qualifications'):
            existing.other_qualifications = merged_data['other_qualifications']
        
        for proj in new_project_experiences:
            if proj.get('project_title'):
                query = EmployeeProjectExperience.query.filter_by(
                    employee_id=existing_id,
                    project_title=proj.get('project_title')
                )
                if proj.get('owner_name'):
                    query = query.filter_by(owner_name=proj.get('owner_name'))
                if proj.get('firm_name'):
                    query = query.filter_by(firm_name=proj.get('firm_name'))
                existing_proj = query.first()
                
                if not existing_proj:
                    exp = EmployeeProjectExperience(
                        employee_id=existing_id,
                        project_title=proj.get('project_title'),
                        location=proj.get('location'),
                        owner_name=proj.get('owner_name'),
                        project_cost=proj.get('project_cost'),
                        year_completed=proj.get('year_completed'),
                        role_performed=proj.get('role_performed'),
                        brief_description=proj.get('brief_description'),
                        firm_name=proj.get('firm_name'),
                        is_current_firm=False
                    )
                    db.session.add(exp)
        
        db.session.commit()
        
        if 'pending_employee_data' in session:
            del session['pending_employee_data']
        
        return jsonify({'success': True, 'id': existing.id, 'message': 'Employee updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai-combine-text', methods=['POST'])
def api_ai_combine_text():
    data = request.json
    text1 = data.get('text1', '')
    text2 = data.get('text2', '')
    field_name = data.get('field_name', 'description')
    
    try:
        combined = combine_and_rewrite_text(text1, text2, field_name)
        return jsonify({'success': True, 'combined_text': combined})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai-combine', methods=['POST'])
def api_ai_combine():
    data = request.json
    values = data.get('values', [])
    field_name = data.get('field_name', 'description')
    
    if len(values) < 2:
        return jsonify({'error': 'Need at least 2 values to combine'}), 400
    
    try:
        combined = values[0]
        for i in range(1, len(values)):
            combined = combine_and_rewrite_text(combined, values[i], field_name)
        return jsonify({'combined': combined})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
