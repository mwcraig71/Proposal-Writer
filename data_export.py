import json
from datetime import datetime, date
from database import db
from models import (
    ClientContact, Firm, Employee, EmployeeAlternateBio, EmployeeProjectExperience,
    ExperienceAlternateDescription, Project, ProjectAlternateDescription, FirmAlternateDescription,
    EmployeeProjectLink, ProjectFirmInvolvement, Proposal, ProposalSelectedEmployee,
    ProposalEmployeeRelevantProject, ProposalSelectedProject, Certification, CertificationType,
    AISettings, EmployeePhoto, ProjectPhoto, FirmPhoto, ProposalSelectedFirmPhoto,
    MarketingPhoto, ProposalSelectedMarketingPhoto, ProposalReference, ProposalIntelligence
)


def serialize_value(value):
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return None
    return value


def serialize_model(obj, exclude_fields=None):
    exclude_fields = exclude_fields or []
    exclude_fields.extend(['_sa_instance_state'])
    data = {}
    for key in obj.__dict__:
        if key not in exclude_fields and not key.startswith('_'):
            data[key] = serialize_value(getattr(obj, key))
    return data


def export_all_data():
    data = {
        'export_date': datetime.utcnow().isoformat(),
        'version': '1.1',  # Added org_chart_data, org_chart_notes to proposals
        'client_contacts': [],
        'firms': [],
        'firm_alternate_descriptions': [],
        'employees': [],
        'employee_alternate_bios': [],
        'employee_project_experiences': [],
        'experience_alternate_descriptions': [],
        'projects': [],
        'project_alternate_descriptions': [],
        'employee_project_links': [],
        'project_firm_involvements': [],
        'proposals': [],
        'proposal_selected_employees': [],
        'proposal_employee_relevant_projects': [],
        'proposal_selected_projects': [],
        'certifications': [],
        'certification_types': [],
        'ai_settings': [],
    }
    
    for contact in ClientContact.query.all():
        data['client_contacts'].append(serialize_model(contact))
    
    for firm in Firm.query.all():
        data['firms'].append(serialize_model(firm))
    
    for desc in FirmAlternateDescription.query.all():
        data['firm_alternate_descriptions'].append(serialize_model(desc))
    
    for emp in Employee.query.all():
        data['employees'].append(serialize_model(emp))
    
    for bio in EmployeeAlternateBio.query.all():
        data['employee_alternate_bios'].append(serialize_model(bio))
    
    for exp in EmployeeProjectExperience.query.all():
        data['employee_project_experiences'].append(serialize_model(exp))
    
    for desc in ExperienceAlternateDescription.query.all():
        data['experience_alternate_descriptions'].append(serialize_model(desc))
    
    for proj in Project.query.all():
        data['projects'].append(serialize_model(proj))
    
    for desc in ProjectAlternateDescription.query.all():
        data['project_alternate_descriptions'].append(serialize_model(desc))
    
    for link in EmployeeProjectLink.query.all():
        data['employee_project_links'].append(serialize_model(link))
    
    for inv in ProjectFirmInvolvement.query.all():
        data['project_firm_involvements'].append(serialize_model(inv))
    
    for prop in Proposal.query.all():
        data['proposals'].append(serialize_model(prop, exclude_fields=['rfp_content']))
    
    for sel in ProposalSelectedEmployee.query.all():
        data['proposal_selected_employees'].append(serialize_model(sel))
    
    for rel in ProposalEmployeeRelevantProject.query.all():
        data['proposal_employee_relevant_projects'].append(serialize_model(rel))
    
    for sel in ProposalSelectedProject.query.all():
        data['proposal_selected_projects'].append(serialize_model(sel))
    
    for cert in Certification.query.all():
        data['certifications'].append(serialize_model(cert, exclude_fields=['pdf_content']))
    
    for ct in CertificationType.query.all():
        data['certification_types'].append(serialize_model(ct))
    
    for setting in AISettings.query.all():
        data['ai_settings'].append(serialize_model(setting))
    
    return data


def parse_date(date_str):
    if not date_str:
        return None
    try:
        if 'T' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return None


def filter_model_fields(model_class, data):
    """Filter data dict to only include valid columns for the model."""
    valid_columns = {col.name for col in model_class.__table__.columns}
    return {k: v for k, v in data.items() if k in valid_columns}


def import_all_data(data, clear_existing=False):
    results = {
        'success': True,
        'imported': {},
        'errors': []
    }
    
    id_maps = {
        'firms': {},
        'employees': {},
        'projects': {},
        'proposals': {},
        'employee_project_experiences': {},
        'proposal_selected_employees': {},
        'firm_alternate_descriptions': {},
        'project_alternate_descriptions': {},
    }
    
    try:
        if clear_existing:
            ProposalEmployeeRelevantProject.query.delete()
            ProposalSelectedProject.query.delete()
            ProposalSelectedEmployee.query.delete()
            ProposalSelectedFirmPhoto.query.delete()
            ProposalSelectedMarketingPhoto.query.delete()
            ProposalReference.query.delete()
            ProposalIntelligence.query.delete()
            Proposal.query.delete()
            EmployeeProjectLink.query.delete()
            ProjectFirmInvolvement.query.delete()
            ExperienceAlternateDescription.query.delete()
            EmployeeProjectExperience.query.delete()
            Certification.query.delete()
            EmployeeAlternateBio.query.delete()
            EmployeePhoto.query.delete()
            Employee.query.delete()
            ProjectAlternateDescription.query.delete()
            ProjectPhoto.query.delete()
            Project.query.delete()
            FirmAlternateDescription.query.delete()
            FirmPhoto.query.delete()
            Firm.query.delete()
            MarketingPhoto.query.delete()
            ClientContact.query.delete()
            CertificationType.query.delete()
            AISettings.query.delete()
            db.session.commit()
        
        count = 0
        for item in data.get('client_contacts', []):
            old_id = item.pop('id', None)
            item.pop('created_at', None)
            item.pop('updated_at', None)
            filtered_item = filter_model_fields(ClientContact, item)
            contact = ClientContact(**filtered_item)
            db.session.add(contact)
            count += 1
        results['imported']['client_contacts'] = count
        db.session.flush()
        
        count = 0
        for item in data.get('firms', []):
            old_id = item.pop('id', None)
            item.pop('created_at', None)
            item.pop('updated_at', None)
            parent_id = item.pop('parent_firm_id', None)
            filtered_item = filter_model_fields(Firm, item)
            firm = Firm(**filtered_item)
            db.session.add(firm)
            db.session.flush()
            id_maps['firms'][old_id] = firm.id
            count += 1
        results['imported']['firms'] = count
        
        for item in data.get('firms', []):
            if item.get('parent_firm_id'):
                old_id = item.get('id')
                new_id = id_maps['firms'].get(old_id)
                parent_new_id = id_maps['firms'].get(item.get('parent_firm_id'))
                if new_id and parent_new_id:
                    firm = Firm.query.get(new_id)
                    if firm:
                        firm.parent_firm_id = parent_new_id
        
        count = 0
        for item in data.get('firm_alternate_descriptions', []):
            old_id = item.pop('id', None)
            item.pop('created_at', None)
            item.pop('updated_at', None)
            old_firm_id = item.pop('firm_id', None)
            new_firm_id = id_maps['firms'].get(old_firm_id)
            if new_firm_id:
                item['firm_id'] = new_firm_id
                filtered_item = filter_model_fields(FirmAlternateDescription, item)
                desc = FirmAlternateDescription(**filtered_item)
                db.session.add(desc)
                db.session.flush()
                id_maps['firm_alternate_descriptions'][old_id] = desc.id
                count += 1
        results['imported']['firm_alternate_descriptions'] = count
        
        count = 0
        for item in data.get('employees', []):
            old_id = item.pop('id', None)
            item.pop('created_at', None)
            item.pop('updated_at', None)
            old_firm_id = item.pop('firm_id', None)
            if old_firm_id:
                item['firm_id'] = id_maps['firms'].get(old_firm_id)
            filtered_item = filter_model_fields(Employee, item)
            emp = Employee(**filtered_item)
            db.session.add(emp)
            db.session.flush()
            id_maps['employees'][old_id] = emp.id
            count += 1
        results['imported']['employees'] = count
        
        count = 0
        for item in data.get('employee_alternate_bios', []):
            old_id = item.pop('id', None)
            item.pop('created_at', None)
            item.pop('updated_at', None)
            old_emp_id = item.pop('employee_id', None)
            new_emp_id = id_maps['employees'].get(old_emp_id)
            if new_emp_id:
                item['employee_id'] = new_emp_id
                filtered_item = filter_model_fields(EmployeeAlternateBio, item)
                bio = EmployeeAlternateBio(**filtered_item)
                db.session.add(bio)
                count += 1
        results['imported']['employee_alternate_bios'] = count
        
        count = 0
        for item in data.get('employee_project_experiences', []):
            old_id = item.pop('id', None)
            item.pop('created_at', None)
            item.pop('updated_at', None)
            old_emp_id = item.pop('employee_id', None)
            new_emp_id = id_maps['employees'].get(old_emp_id)
            if new_emp_id:
                item['employee_id'] = new_emp_id
                filtered_item = filter_model_fields(EmployeeProjectExperience, item)
                exp = EmployeeProjectExperience(**filtered_item)
                db.session.add(exp)
                db.session.flush()
                id_maps['employee_project_experiences'][old_id] = exp.id
                count += 1
        results['imported']['employee_project_experiences'] = count
        
        count = 0
        for item in data.get('experience_alternate_descriptions', []):
            old_id = item.pop('id', None)
            item.pop('created_at', None)
            item.pop('updated_at', None)
            old_exp_id = item.pop('experience_id', None)
            new_exp_id = id_maps['employee_project_experiences'].get(old_exp_id)
            if new_exp_id:
                item['experience_id'] = new_exp_id
                filtered_item = filter_model_fields(ExperienceAlternateDescription, item)
                desc = ExperienceAlternateDescription(**filtered_item)
                db.session.add(desc)
                count += 1
        results['imported']['experience_alternate_descriptions'] = count
        
        count = 0
        for item in data.get('projects', []):
            old_id = item.pop('id', None)
            item.pop('created_at', None)
            item.pop('updated_at', None)
            filtered_item = filter_model_fields(Project, item)
            proj = Project(**filtered_item)
            db.session.add(proj)
            db.session.flush()
            id_maps['projects'][old_id] = proj.id
            count += 1
        results['imported']['projects'] = count
        
        count = 0
        for item in data.get('project_alternate_descriptions', []):
            old_id = item.pop('id', None)
            item.pop('created_at', None)
            item.pop('updated_at', None)
            old_proj_id = item.pop('project_id', None)
            new_proj_id = id_maps['projects'].get(old_proj_id)
            if new_proj_id:
                item['project_id'] = new_proj_id
                filtered_item = filter_model_fields(ProjectAlternateDescription, item)
                desc = ProjectAlternateDescription(**filtered_item)
                db.session.add(desc)
                db.session.flush()
                id_maps['project_alternate_descriptions'][old_id] = desc.id
                count += 1
        results['imported']['project_alternate_descriptions'] = count
        
        count = 0
        for item in data.get('employee_project_links', []):
            old_id = item.pop('id', None)
            item.pop('created_at', None)
            old_emp_id = item.pop('employee_id', None)
            old_proj_id = item.pop('project_id', None)
            new_emp_id = id_maps['employees'].get(old_emp_id)
            new_proj_id = id_maps['projects'].get(old_proj_id)
            if new_emp_id and new_proj_id:
                item['employee_id'] = new_emp_id
                item['project_id'] = new_proj_id
                filtered_item = filter_model_fields(EmployeeProjectLink, item)
                link = EmployeeProjectLink(**filtered_item)
                db.session.add(link)
                count += 1
        results['imported']['employee_project_links'] = count
        
        count = 0
        for item in data.get('project_firm_involvements', []):
            old_id = item.pop('id', None)
            old_proj_id = item.pop('project_id', None)
            old_firm_id = item.pop('firm_id', None)
            new_proj_id = id_maps['projects'].get(old_proj_id)
            new_firm_id = id_maps['firms'].get(old_firm_id)
            if new_proj_id and new_firm_id:
                item['project_id'] = new_proj_id
                item['firm_id'] = new_firm_id
                filtered_item = filter_model_fields(ProjectFirmInvolvement, item)
                inv = ProjectFirmInvolvement(**filtered_item)
                db.session.add(inv)
                count += 1
        results['imported']['project_firm_involvements'] = count
        
        count = 0
        for item in data.get('proposals', []):
            old_id = item.pop('id', None)
            item.pop('created_at', None)
            item.pop('updated_at', None)
            old_firm_id = item.pop('firm_id', None)
            old_bio_id = item.pop('firm_bio_alternate_id', None)
            if old_firm_id:
                item['firm_id'] = id_maps['firms'].get(old_firm_id)
            if old_bio_id:
                item['firm_bio_alternate_id'] = id_maps['firm_alternate_descriptions'].get(old_bio_id)
            filtered_item = filter_model_fields(Proposal, item)
            prop = Proposal(**filtered_item)
            db.session.add(prop)
            db.session.flush()
            id_maps['proposals'][old_id] = prop.id
            count += 1
        results['imported']['proposals'] = count
        
        count = 0
        for item in data.get('proposal_selected_employees', []):
            old_id = item.pop('id', None)
            old_prop_id = item.pop('proposal_id', None)
            old_emp_id = item.pop('employee_id', None)
            new_prop_id = id_maps['proposals'].get(old_prop_id)
            new_emp_id = id_maps['employees'].get(old_emp_id)
            if new_prop_id and new_emp_id:
                item['proposal_id'] = new_prop_id
                item['employee_id'] = new_emp_id
                filtered_item = filter_model_fields(ProposalSelectedEmployee, item)
                sel = ProposalSelectedEmployee(**filtered_item)
                db.session.add(sel)
                db.session.flush()
                id_maps['proposal_selected_employees'][old_id] = sel.id
                count += 1
        results['imported']['proposal_selected_employees'] = count
        
        count = 0
        for item in data.get('proposal_employee_relevant_projects', []):
            old_id = item.pop('id', None)
            old_sel_id = item.pop('proposal_selected_employee_id', None)
            old_proj_id = item.pop('project_id', None)
            new_sel_id = id_maps['proposal_selected_employees'].get(old_sel_id)
            new_proj_id = id_maps['projects'].get(old_proj_id)
            if new_sel_id and new_proj_id:
                item['proposal_selected_employee_id'] = new_sel_id
                item['project_id'] = new_proj_id
                filtered_item = filter_model_fields(ProposalEmployeeRelevantProject, item)
                rel = ProposalEmployeeRelevantProject(**filtered_item)
                db.session.add(rel)
                count += 1
        results['imported']['proposal_employee_relevant_projects'] = count
        
        count = 0
        for item in data.get('proposal_selected_projects', []):
            old_id = item.pop('id', None)
            old_prop_id = item.pop('proposal_id', None)
            old_proj_id = item.pop('project_id', None)
            old_alt_id = item.pop('alternate_description_id', None)
            new_prop_id = id_maps['proposals'].get(old_prop_id)
            new_proj_id = id_maps['projects'].get(old_proj_id)
            if new_prop_id and new_proj_id:
                item['proposal_id'] = new_prop_id
                item['project_id'] = new_proj_id
                if old_alt_id:
                    item['alternate_description_id'] = id_maps['project_alternate_descriptions'].get(old_alt_id)
                filtered_item = filter_model_fields(ProposalSelectedProject, item)
                sel = ProposalSelectedProject(**filtered_item)
                db.session.add(sel)
                count += 1
        results['imported']['proposal_selected_projects'] = count
        
        count = 0
        for item in data.get('certifications', []):
            old_id = item.pop('id', None)
            item.pop('created_at', None)
            item.pop('updated_at', None)
            old_emp_id = item.pop('employee_id', None)
            new_emp_id = id_maps['employees'].get(old_emp_id)
            if new_emp_id:
                item['employee_id'] = new_emp_id
                if item.get('expiration_date'):
                    item['expiration_date'] = parse_date(item['expiration_date'])
                if item.get('issue_date'):
                    item['issue_date'] = parse_date(item['issue_date'])
                filtered_item = filter_model_fields(Certification, item)
                cert = Certification(**filtered_item)
                db.session.add(cert)
                count += 1
        results['imported']['certifications'] = count
        
        count = 0
        for item in data.get('certification_types', []):
            old_id = item.pop('id', None)
            item.pop('created_at', None)
            existing = CertificationType.query.filter_by(
                name=item.get('name'),
                category=item.get('category')
            ).first()
            if not existing:
                filtered_item = filter_model_fields(CertificationType, item)
                ct = CertificationType(**filtered_item)
                db.session.add(ct)
                count += 1
        results['imported']['certification_types'] = count
        
        count = 0
        for item in data.get('ai_settings', []):
            old_id = item.pop('id', None)
            item.pop('updated_at', None)
            existing = AISettings.query.filter_by(setting_key=item.get('setting_key')).first()
            if existing:
                existing.setting_value = item.get('setting_value')
            else:
                filtered_item = filter_model_fields(AISettings, item)
                setting = AISettings(**filtered_item)
                db.session.add(setting)
            count += 1
        results['imported']['ai_settings'] = count
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        results['success'] = False
        results['errors'].append(str(e))
    
    return results
