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
    google_drive_folder_url = db.Column(db.String(500))
    
    stat_bridges_inspected = db.Column(db.Integer)
    stat_bridges_inspected_updated = db.Column(db.DateTime)
    stat_length_bridge_inspected = db.Column(db.String(100))
    stat_length_bridge_inspected_updated = db.Column(db.DateTime)
    stat_fcm_bridge_inspections = db.Column(db.Integer)
    stat_fcm_bridge_inspections_updated = db.Column(db.DateTime)
    stat_load_ratings_performed = db.Column(db.Integer)
    stat_load_ratings_performed_updated = db.Column(db.DateTime)
    stat_critical_findings = db.Column(db.Integer)
    stat_critical_findings_updated = db.Column(db.DateTime)
    stat_timber_inspections = db.Column(db.Integer)
    stat_timber_inspections_updated = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employees = db.relationship('Employee', backref='firm', lazy=True)
    branch_offices = db.relationship('Firm', backref=db.backref('parent_firm', remote_side=[id]), lazy=True)


class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    firm_id = db.Column(db.Integer, db.ForeignKey('firms.id'), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    nickname = db.Column(db.String(100))
    title = db.Column(db.String(255))
    role = db.Column(db.String(255))
    years_experience_total = db.Column(db.Integer)
    years_experience_firm = db.Column(db.Integer)
    career_start_date = db.Column(db.Date, nullable=True)
    firm_hire_date = db.Column(db.Date, nullable=True)
    bio = db.Column(db.Text)
    education = db.Column(db.Text)
    registrations = db.Column(db.Text)
    training = db.Column(db.Text)
    other_qualifications = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    archived = db.Column(db.Boolean, default=False, nullable=False, server_default='false')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project_links = db.relationship('EmployeeProjectLink', backref='employee', lazy=True)
    
    @property
    def display_name(self):
        """Returns the display name combining first and last names (no middle name)"""
        if self.first_name or self.last_name:
            parts = [self.first_name or '', self.last_name or '']
            return ' '.join(p for p in parts if p).strip()
        return self.name


class EmployeeAlternateBio(db.Model):
    """Stores alternate bio versions for employees - useful for merging imported bios"""
    __tablename__ = 'employee_alternate_bios'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    label = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref=db.backref('alternate_bios', lazy=True, cascade='all, delete-orphan'))


class EmployeeProjectExperience(db.Model):
    """Stores project experience from employee resumes - may include projects from previous employers"""
    __tablename__ = 'employee_project_experiences'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    linked_project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    selected_alt_description_id = db.Column(db.Integer, db.ForeignKey('experience_alternate_descriptions.id'), nullable=True)
    project_title = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(255))
    owner_name = db.Column(db.String(255))
    project_cost = db.Column(db.String(100))
    year_completed = db.Column(db.String(50))
    role_performed = db.Column(db.String(255))
    brief_description = db.Column(db.Text)
    firm_name = db.Column(db.String(255))
    is_current_firm = db.Column(db.Boolean, default=False)
    sf330_include = db.Column(db.Boolean, default=False)
    resume_order = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref=db.backref('project_experiences', lazy=True, cascade='all, delete-orphan'))
    linked_project = db.relationship('Project', backref=db.backref('personnel_writeups', lazy=True))
    selected_alt_description = db.relationship('ExperienceAlternateDescription', foreign_keys=[selected_alt_description_id], post_update=True)
    
    @property
    def active_description(self):
        """Returns the selected alternate description if set, otherwise the main brief_description"""
        if self.selected_alt_description_id and self.selected_alt_description:
            return self.selected_alt_description.description
        return self.brief_description
    
    @property
    def active_description_label(self):
        """Returns the label of the active description"""
        if self.selected_alt_description_id and self.selected_alt_description:
            return self.selected_alt_description.label
        return "Main Description"


class ExperienceAlternateDescription(db.Model):
    """Stores alternate brief descriptions for employee project experience (Section E resume projects)"""
    __tablename__ = 'experience_alternate_descriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    experience_id = db.Column(db.Integer, db.ForeignKey('employee_project_experiences.id'), nullable=False)
    label = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    experience = db.relationship('EmployeeProjectExperience', foreign_keys=[experience_id], backref=db.backref('alternate_descriptions', lazy=True, cascade='all, delete-orphan'))


class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    firm_id = db.Column(db.Integer, db.ForeignKey('firms.id'), nullable=True)
    title = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(255))
    year_completed_professional = db.Column(db.String(50))
    year_completed_construction = db.Column(db.String(50))
    owner_name = db.Column(db.String(255))
    owner_contact_name = db.Column(db.String(255))
    owner_contact_phone = db.Column(db.String(50))
    owner_contact_email = db.Column(db.String(255))
    owner_contact_id = db.Column(db.Integer, db.ForeignKey('client_contacts.id'), nullable=True)
    project_cost = db.Column(db.String(255))
    project_delivery_method = db.Column(db.String(255))
    brief_description = db.Column(db.Text)
    relevance_writeup = db.Column(db.Text)
    is_with_other_firm = db.Column(db.Boolean, default=False)
    other_firm_name = db.Column(db.String(255))
    project_type = db.Column(db.String(50), default='contract')
    parent_contract_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    archived = db.Column(db.Boolean, default=False, nullable=False, server_default='false')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee_links = db.relationship('EmployeeProjectLink', backref='project', lazy=True)
    firm_involvements = db.relationship('ProjectFirmInvolvement', backref='project', lazy=True)
    firm = db.relationship('Firm', backref=db.backref('projects', lazy=True))
    task_orders = db.relationship('Project', backref=db.backref('parent_contract', remote_side='Project.id'), lazy=True, foreign_keys='Project.parent_contract_id')


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
    win_theme = db.Column(db.Text)  # Key messages and strategy for winning
    proposal_outline = db.Column(db.Text)  # AI-generated proposal outline based on RFP and data
    proposal_outline_instructions = db.Column(db.Text)  # Custom instructions used for outline
    cover_letter = db.Column(db.Text)
    written_sections = db.Column(db.Text)
    org_chart_data = db.Column(db.Text)  # JSON string storing org chart nodes and edges
    org_chart_notes = db.Column(db.Text)  # Global notes for the org chart
    saved_org_chart_id = db.Column(db.Integer, db.ForeignKey('saved_org_charts.id'), nullable=True)
    status = db.Column(db.String(50), default='draft')
    archived = db.Column(db.Boolean, default=False, nullable=False, server_default='false')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    firm = db.relationship('Firm', backref='proposals')
    firm_bio_alternate = db.relationship('FirmAlternateDescription')
    saved_org_chart = db.relationship('SavedOrgChart', backref='proposals')
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
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    experience_id = db.Column(db.Integer, db.ForeignKey('employee_project_experiences.id'), nullable=True)
    display_order = db.Column(db.Integer, default=0)
    
    project = db.relationship('Project')
    experience = db.relationship('EmployeeProjectExperience')


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


class CertificationType(db.Model):
    """Master list of certification types for the checklist when adding personnel"""
    __tablename__ = 'certification_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100))  # 'NHI', 'Safety', 'SPRAT', 'Drone', 'PE License'
    cert_type = db.Column(db.String(100), default='certification')  # 'training', 'license', 'certification'
    default_state = db.Column(db.String(50))  # For PE licenses, default state
    has_levels = db.Column(db.Boolean, default=False)  # True for SPRAT which has levels
    has_expiration = db.Column(db.Boolean, default=True)  # Most certs expire
    sort_order = db.Column(db.Integer, default=0)  # For display ordering within category
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('name', 'category', name='uq_cert_type_name_category'),
    )


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


class EmployeePhoto(db.Model):
    """Stores photo references for employees - actual files in object storage"""
    __tablename__ = 'employee_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    content_type = db.Column(db.String(100))
    is_primary = db.Column(db.Boolean, default=False)
    include_in_resume = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    employee = db.relationship('Employee', backref=db.backref('photos', lazy=True, cascade='all, delete-orphan'))


class ProjectPhoto(db.Model):
    """Stores photo references for projects - actual files in object storage"""
    __tablename__ = 'project_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    content_type = db.Column(db.String(100))
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    project = db.relationship('Project', backref=db.backref('photos', lazy=True, cascade='all, delete-orphan'))


class FirmPhoto(db.Model):
    """Stores photo references for firms - actual files in object storage"""
    __tablename__ = 'firm_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    firm_id = db.Column(db.Integer, db.ForeignKey('firms.id'), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    content_type = db.Column(db.String(100))
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    firm = db.relationship('Firm', backref=db.backref('photos', lazy=True, cascade='all, delete-orphan'))


class FirmDocument(db.Model):
    """Stores document references for firms - PDFs, Word docs, Excel files in object storage"""
    __tablename__ = 'firm_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    firm_id = db.Column(db.Integer, db.ForeignKey('firms.id'), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    content_type = db.Column(db.String(100))
    document_type = db.Column(db.String(50))  # 'pdf', 'word', 'excel', 'other'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    firm = db.relationship('Firm', backref=db.backref('documents', lazy=True, cascade='all, delete-orphan'))


class EmployeeDocument(db.Model):
    """Stores document references for employees - PDFs, Word docs in object storage"""
    __tablename__ = 'employee_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    content_type = db.Column(db.String(100))
    document_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    employee = db.relationship('Employee', backref=db.backref('documents', lazy=True, cascade='all, delete-orphan'))


class ProjectDocument(db.Model):
    """Stores document references for projects - PDFs, Word docs, Excel files in object storage"""
    __tablename__ = 'project_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    content_type = db.Column(db.String(100))
    document_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    project = db.relationship('Project', backref=db.backref('documents', lazy=True, cascade='all, delete-orphan'))


class SavedOrgChart(db.Model):
    __tablename__ = 'saved_org_charts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500), nullable=False)
    org_chart_data = db.Column(db.Text)
    org_chart_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProposalSelectedFirmPhoto(db.Model):
    """Junction table for firm photos selected for a proposal"""
    __tablename__ = 'proposal_selected_firm_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'), nullable=False)
    firm_photo_id = db.Column(db.Integer, db.ForeignKey('firm_photos.id'), nullable=False)
    display_order = db.Column(db.Integer, default=0)
    
    proposal = db.relationship('Proposal', backref=db.backref('selected_firm_photos', lazy=True, cascade='all, delete-orphan'))
    firm_photo = db.relationship('FirmPhoto')


class MarketingPhoto(db.Model):
    """Stores marketing photos with tags for filtering"""
    __tablename__ = 'marketing_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(500), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(500))
    tags = db.Column(db.Text)  # Comma-separated tags like "#bridge,#inspection,#team"
    file_size = db.Column(db.Integer)
    content_type = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_tags_list(self):
        """Return tags as a list"""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]
    
    def set_tags_from_list(self, tags_list):
        """Set tags from a list"""
        self.tags = ','.join(tags_list) if tags_list else ''


class ProposalSelectedMarketingPhoto(db.Model):
    """Junction table for marketing photos selected for a proposal"""
    __tablename__ = 'proposal_selected_marketing_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'), nullable=False)
    marketing_photo_id = db.Column(db.Integer, db.ForeignKey('marketing_photos.id'), nullable=False)
    display_order = db.Column(db.Integer, default=0)
    
    proposal = db.relationship('Proposal', backref=db.backref('selected_marketing_photos', lazy=True, cascade='all, delete-orphan'))
    marketing_photo = db.relationship('MarketingPhoto')


class ProposalReference(db.Model):
    """Stores previous proposal documents uploaded as reference for AI-generated content"""
    __tablename__ = 'proposal_references'
    
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    file_content = db.Column(db.LargeBinary)
    extracted_text = db.Column(db.Text)
    file_size = db.Column(db.Integer)
    content_type = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    proposal = db.relationship('Proposal', backref=db.backref('reference_documents', lazy=True, cascade='all, delete-orphan'))


class ProposalIntelligence(db.Model):
    """Stores intelligence documents (competitor info, client background, etc.) for proposal writing"""
    __tablename__ = 'proposal_intelligence'
    
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    file_content = db.Column(db.LargeBinary)
    extracted_text = db.Column(db.Text)
    description = db.Column(db.String(500))  # Brief description of what this document contains
    file_size = db.Column(db.Integer)
    content_type = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    proposal = db.relationship('Proposal', backref=db.backref('intelligence_documents', lazy=True, cascade='all, delete-orphan'))


class ProposalSavedResponse(db.Model):
    """Stores AI-generated responses saved by the user for a proposal"""
    __tablename__ = 'proposal_saved_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'), nullable=False)
    prompt = db.Column(db.Text)
    response = db.Column(db.Text, nullable=False)
    label = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    proposal = db.relationship('Proposal', backref=db.backref('saved_responses', lazy=True, cascade='all, delete-orphan'))


class Response(db.Model):
    """Stores reusable question/response library for proposals"""
    __tablename__ = 'responses'
    
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer)
    client = db.Column(db.String(255))
    project_type = db.Column(db.String(255))
    contract = db.Column(db.String(500))
    firm = db.Column(db.String(255))
    grade = db.Column(db.String(10))
    question = db.Column(db.Text)
    response = db.Column(db.Text)
    tags = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_tags_list(self):
        """Return tags as a list"""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]
    
    def set_tags_from_list(self, tags_list):
        """Set tags from a list"""
        self.tags = ','.join(tags_list) if tags_list else ''


class ProposalLinkedResponse(db.Model):
    """Junction table for responses linked to a proposal"""
    __tablename__ = 'proposal_linked_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'), nullable=False)
    response_id = db.Column(db.Integer, db.ForeignKey('responses.id'), nullable=False)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    proposal = db.relationship('Proposal', backref=db.backref('linked_responses', lazy=True, cascade='all, delete-orphan'))
    response = db.relationship('Response', backref=db.backref('proposal_links', lazy=True, cascade='all, delete-orphan'))
    
    __table_args__ = (db.UniqueConstraint('proposal_id', 'response_id', name='unique_proposal_response'),)


class Reference(db.Model):
    """Stores client/project references including performance evaluations and quotes"""
    __tablename__ = 'references'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    project = db.relationship('Project', backref='references')
    client = db.Column(db.String(255))
    agency = db.Column(db.String(255))
    project_name = db.Column(db.String(500))
    contract_number = db.Column(db.String(100))
    project_id_number = db.Column(db.String(100))
    evaluation_date = db.Column(db.Date)
    evaluation_period = db.Column(db.String(50))
    final_score = db.Column(db.Float)
    schedule_score = db.Column(db.Float)
    quality_score = db.Column(db.Float)
    responsiveness_score = db.Column(db.Float)
    key_staff_score = db.Column(db.Float)
    dbe_score = db.Column(db.Float)
    pm_performance_score = db.Column(db.Float)
    score_summary = db.Column(db.Text)
    quotes = db.Column(db.Text)
    evaluator_name = db.Column(db.String(255))
    evaluator_title = db.Column(db.String(255))
    consultant_pm = db.Column(db.String(255))
    firm = db.Column(db.String(255))
    services_description = db.Column(db.Text)
    activities_evaluated = db.Column(db.Text)
    personnel_tags = db.Column(db.Text)
    pdf_filename = db.Column(db.String(500))
    pdf_object_key = db.Column(db.String(500))
    reference_type = db.Column(db.String(50), default='evaluation')
    is_final_evaluation = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_personnel_tags_list(self):
        """Return personnel tags as a list"""
        if not self.personnel_tags:
            return []
        return [t.strip() for t in self.personnel_tags.split(',') if t.strip()]
    
    def set_personnel_tags_from_list(self, tags_list):
        """Set personnel tags from a list"""
        self.personnel_tags = ','.join(tags_list) if tags_list else ''


class ProposalLinkedReference(db.Model):
    """Junction table for references linked to a proposal"""
    __tablename__ = 'proposal_linked_references'
    
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'), nullable=False)
    reference_id = db.Column(db.Integer, db.ForeignKey('references.id'), nullable=False)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    proposal = db.relationship('Proposal', backref=db.backref('linked_references', lazy=True, cascade='all, delete-orphan'))
    reference = db.relationship('Reference', backref=db.backref('proposal_links', lazy=True, cascade='all, delete-orphan'))
    
    __table_args__ = (db.UniqueConstraint('proposal_id', 'reference_id', name='unique_proposal_reference'),)


class ProjectLinkedReference(db.Model):
    __tablename__ = 'project_linked_references'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    reference_id = db.Column(db.Integer, db.ForeignKey('references.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    project = db.relationship('Project', backref=db.backref('linked_references', lazy=True, cascade='all, delete-orphan'))
    reference = db.relationship('Reference', backref=db.backref('project_links', lazy=True, cascade='all, delete-orphan'))
    
    __table_args__ = (db.UniqueConstraint('project_id', 'reference_id', name='unique_project_reference'),)


class EmployeeLinkedReference(db.Model):
    __tablename__ = 'employee_linked_references'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    reference_id = db.Column(db.Integer, db.ForeignKey('references.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    employee = db.relationship('Employee', backref=db.backref('linked_references', lazy=True, cascade='all, delete-orphan'))
    reference = db.relationship('Reference', backref=db.backref('employee_links', lazy=True, cascade='all, delete-orphan'))
    
    __table_args__ = (db.UniqueConstraint('employee_id', 'reference_id', name='unique_employee_reference'),)


class ResumeGraphic(db.Model):
    __tablename__ = 'resume_graphics'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500), nullable=False)
    graphic_type = db.Column(db.String(50), nullable=False)  # 'challenge-solution', 'competency-badge', 'key-staff'
    payload = db.Column(db.Text, nullable=False)  # JSON data with pairs/badges/staff, sizePreset, width, fontScale
    tags = db.Column(db.String(500))
    notes = db.Column(db.Text)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    include_in_resume = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref=db.backref('resume_graphics', lazy=True))
    project = db.relationship('Project', backref=db.backref('resume_graphics', lazy=True))


class GraphicScenario(db.Model):
    __tablename__ = 'graphic_scenarios'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(100))
    challenge = db.Column(db.Text)
    solution = db.Column(db.Text)
    type = db.Column(db.String(50), default='challenge-solution')
    payload = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)