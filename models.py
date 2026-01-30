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
    first_name = db.Column(db.String(100))
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    nickname = db.Column(db.String(100))
    title = db.Column(db.String(255))
    role = db.Column(db.String(255))
    years_experience_total = db.Column(db.Integer)
    years_experience_firm = db.Column(db.Integer)
    bio = db.Column(db.Text)
    education = db.Column(db.Text)
    registrations = db.Column(db.Text)
    training = db.Column(db.Text)
    other_qualifications = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project_links = db.relationship('EmployeeProjectLink', backref='employee', lazy=True)
    
    @property
    def display_name(self):
        """Returns the full display name combining first, middle, last names"""
        if self.first_name or self.last_name:
            parts = [self.first_name or '', self.middle_name or '', self.last_name or '']
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
    win_theme = db.Column(db.Text)  # Key messages and strategy for winning
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
