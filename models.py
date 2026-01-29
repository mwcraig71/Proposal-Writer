from datetime import datetime
from database import db


class ClientContact(db.Model):
    __tablename__ = 'client_contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    agency = db.Column(db.String(255))
    role = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    physical_street = db.Column(db.String(255))
    physical_city = db.Column(db.String(100))
    physical_state = db.Column(db.String(50))
    physical_zip = db.Column(db.String(20))
    mailing_street = db.Column(db.String(255))
    mailing_city = db.Column(db.String(100))
    mailing_state = db.Column(db.String(50))
    mailing_zip = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Firm(db.Model):
    __tablename__ = 'firms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    uei = db.Column(db.String(50))
    street_address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    country = db.Column(db.String(100), default='USA')
    year_established = db.Column(db.Integer)
    ownership_type = db.Column(db.String(100))
    is_small_business = db.Column(db.Boolean, default=False)
    small_business_categories = db.Column(db.Text)
    phone = db.Column(db.String(50))
    fax = db.Column(db.String(50))
    email = db.Column(db.String(255))
    point_of_contact_name = db.Column(db.String(255))
    point_of_contact_title = db.Column(db.String(255))
    bio = db.Column(db.Text)
    is_branch = db.Column(db.Boolean, default=False)
    parent_firm_id = db.Column(db.Integer, db.ForeignKey('firms.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employees = db.relationship('Employee', backref='firm', lazy=True)
    branch_offices = db.relationship('Firm', backref=db.backref('parent_firm', remote_side=[id]), lazy=True)


class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    firm_id = db.Column(db.Integer, db.ForeignKey('firms.id'), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255))
    role = db.Column(db.String(255))
    years_experience_total = db.Column(db.Integer)
    years_experience_firm = db.Column(db.Integer)
    education = db.Column(db.Text)
    registrations = db.Column(db.Text)
    training = db.Column(db.Text)
    other_qualifications = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project_links = db.relationship('EmployeeProjectLink', backref='employee', lazy=True)


class EmployeeProjectExperience(db.Model):
    """Stores project experience from employee resumes - may include projects from previous employers"""
    __tablename__ = 'employee_project_experiences'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    project_title = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(255))
    owner_name = db.Column(db.String(255))
    project_cost = db.Column(db.String(100))
    year_completed = db.Column(db.String(50))
    role_performed = db.Column(db.String(255))
    brief_description = db.Column(db.Text)
    firm_name = db.Column(db.String(255))
    is_current_firm = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref=db.backref('project_experiences', lazy=True, cascade='all, delete-orphan'))


class ExperienceAlternateDescription(db.Model):
    """Stores alternate brief descriptions for employee project experience (Section E resume projects)"""
    __tablename__ = 'experience_alternate_descriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    experience_id = db.Column(db.Integer, db.ForeignKey('employee_project_experiences.id'), nullable=False)
    label = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    experience = db.relationship('EmployeeProjectExperience', backref=db.backref('alternate_descriptions', lazy=True, cascade='all, delete-orphan'))


class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(255))
    year_completed_professional = db.Column(db.String(50))
    year_completed_construction = db.Column(db.String(50))
    owner_name = db.Column(db.String(255))
    owner_contact_name = db.Column(db.String(255))
    owner_contact_phone = db.Column(db.String(50))
    project_cost = db.Column(db.String(100))
    project_delivery_method = db.Column(db.String(255))
    brief_description = db.Column(db.Text)
    relevance_writeup = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee_links = db.relationship('EmployeeProjectLink', backref='project', lazy=True)
    firm_involvements = db.relationship('ProjectFirmInvolvement', backref='project', lazy=True)


class ProjectAlternateDescription(db.Model):
    """Stores alternate brief descriptions for Section F, Block 24"""
    __tablename__ = 'project_alternate_descriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    label = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = db.relationship('Project', backref=db.backref('alternate_descriptions', lazy=True, cascade='all, delete-orphan'))


class FirmAlternateDescription(db.Model):
    """Stores alternate bio/writeup versions for firms"""
    __tablename__ = 'firm_alternate_descriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    firm_id = db.Column(db.Integer, db.ForeignKey('firms.id'), nullable=False)
    label = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    firm = db.relationship('Firm', backref=db.backref('alternate_descriptions', lazy=True, cascade='all, delete-orphan'))


class EmployeeProjectLink(db.Model):
    __tablename__ = 'employee_project_links'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    role_on_project = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('employee_id', 'project_id', name='unique_employee_project'),)


class ProjectFirmInvolvement(db.Model):
    __tablename__ = 'project_firm_involvements'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    firm_id = db.Column(db.Integer, db.ForeignKey('firms.id'), nullable=False)
    role = db.Column(db.String(255))


class Proposal(db.Model):
    __tablename__ = 'proposals'
    
    id = db.Column(db.Integer, primary_key=True)
    tracking_number = db.Column(db.String(100), nullable=True)
    name = db.Column(db.String(500), nullable=False)
    contract_title = db.Column(db.String(500))
    contract_location = db.Column(db.String(255))
    public_notice_date = db.Column(db.String(100))
    solicitation_number = db.Column(db.String(255))
    firm_id = db.Column(db.Integer, db.ForeignKey('firms.id'), nullable=True)
    firm_bio_alternate_id = db.Column(db.Integer, db.ForeignKey('firm_alternate_descriptions.id'), nullable=True)
    rfp_filename = db.Column(db.String(500))
    rfp_content = db.Column(db.LargeBinary)
    rfp_text = db.Column(db.Text)
    cover_letter = db.Column(db.Text)
    written_sections = db.Column(db.Text)
    status = db.Column(db.String(50), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    firm = db.relationship('Firm', backref='proposals')
    firm_bio_alternate = db.relationship('FirmAlternateDescription')
    selected_employees = db.relationship('ProposalSelectedEmployee', backref='proposal', lazy=True, cascade='all, delete-orphan')
    selected_projects = db.relationship('ProposalSelectedProject', backref='proposal', lazy=True, cascade='all, delete-orphan')


class ProposalSelectedEmployee(db.Model):
    __tablename__ = 'proposal_selected_employees'
    
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    role_in_contract = db.Column(db.String(255))
    display_order = db.Column(db.Integer, default=0)
    
    employee = db.relationship('Employee')
    relevant_projects = db.relationship('ProposalEmployeeRelevantProject', backref='proposal_employee', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('proposal_id', 'employee_id', name='unique_proposal_employee'),)


class ProposalEmployeeRelevantProject(db.Model):
    __tablename__ = 'proposal_employee_relevant_projects'
    
    id = db.Column(db.Integer, primary_key=True)
    proposal_selected_employee_id = db.Column(db.Integer, db.ForeignKey('proposal_selected_employees.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    display_order = db.Column(db.Integer, default=0)
    
    project = db.relationship('Project')


class ProposalSelectedProject(db.Model):
    __tablename__ = 'proposal_selected_projects'
    
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    display_order = db.Column(db.Integer, default=0)
    custom_writeup = db.Column(db.Text)
    alternate_description_id = db.Column(db.Integer, db.ForeignKey('project_alternate_descriptions.id'), nullable=True)
    
    project = db.relationship('Project')
    alternate_description = db.relationship('ProjectAlternateDescription')
    
    __table_args__ = (db.UniqueConstraint('proposal_id', 'project_id', name='unique_proposal_project'),)


class Certification(db.Model):
    """Stores employee certifications, licenses, and training records with PDF documentation"""
    __tablename__ = 'certifications'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    cert_type = db.Column(db.String(100), nullable=False)  # 'training', 'license', 'certification'
    category = db.Column(db.String(100))  # 'NHI', 'Safety', 'SPRAT', 'Drone', 'PE License'
    name = db.Column(db.String(255), nullable=False)  # e.g., 'NHI-130055', 'OSHA-10', 'PE'
    state = db.Column(db.String(50))  # For PE licenses
    level = db.Column(db.String(50))  # For SPRAT levels
    status = db.Column(db.String(50))  # 'completed', 'active', 'expired', 'yes', 'registered'
    expiration_date = db.Column(db.Date)
    issue_date = db.Column(db.Date)
    license_number = db.Column(db.String(100))
    pdf_filename = db.Column(db.String(500))
    pdf_content = db.Column(db.LargeBinary)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref=db.backref('certifications', lazy=True, cascade='all, delete-orphan'))


class AISettings(db.Model):
    __tablename__ = 'ai_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_value(key, default=''):
        setting = AISettings.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else default
    
    @staticmethod
    def set_value(key, value):
        from database import db
        setting = AISettings.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = value
        else:
            setting = AISettings(setting_key=key, setting_value=value)
            db.session.add(setting)
        db.session.commit()
