# SF330 AI Automation System

## Overview
A Flask-based web application that automates the creation of Federal Standard Form 330 (SF330) Architect-Engineer Qualifications. The system uses Google Gemini AI to parse uploaded documents and provides a wizard-style interface to build proposals.

## Current State
MVP implementation complete with:
- AI-powered document parsing (resumes, project sheets, firm profiles)
- Database management for Firms, Employees, Projects
- Proposal builder wizard with 4 steps
- Section G Matrix auto-generation
- PDF generation capability

## Tech Stack
- **Backend:** Python/Flask with SQLAlchemy ORM
- **Database:** PostgreSQL
- **AI:** Google Gemini via Replit AI Integrations
- **Frontend:** Jinja2 templates with Tailwind CSS

## Project Structure
```
/
├── main.py              # Flask app initialization
├── models.py            # SQLAlchemy database models
├── routes.py            # All HTTP routes
├── gemini_service.py    # AI parsing functions
├── document_parser.py   # File text extraction
├── pdf_generator.py     # SF330 PDF generation
├── templates/           # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── upload.html
│   ├── employees.html
│   ├── projects.html
│   ├── firms.html
│   ├── proposals.html
│   └── proposal_wizard_*.html
└── attached_assets/     # SF330 PDF template
```

## Key Features
1. **Document Upload & AI Parsing** - Upload PDF/DOCX/XLSX files, AI extracts structured data
2. **Data Management** - CRUD operations for firms, employees, and projects
3. **Proposal Builder** - Multi-step wizard to create SF330 submissions
4. **Section G Matrix** - Auto-generates personnel-project participation grid
5. **PDF Generation** - Fills SF330 template with proposal data

## Database Schema
- **Firms** - Company/branch office data (Part II)
- **Employees** - Personnel resumes (Section E)
- **Projects** - Example projects (Section F - firm's project database)
- **ProjectAlternateDescription** - Alternate brief descriptions for projects (Section F, Block 24)
- **EmployeeProjectExperience** - Project experience from resumes (may include projects from previous employers)
- **ExperienceAlternateDescription** - Alternate brief descriptions for resume project experiences
- **EmployeeProjectLink** - Many-to-many for Section G matrix (links employees to firm projects)
- **Proposals** - SF330 submission containers
- **ProposalSelectedEmployee/Project** - Junction tables (ProposalSelectedProject now includes alternate_description_id)
- **Certification** - Employee certifications, licenses, and training records with PDF storage

## Running the Application
The app runs on port 5000. Access via the webview.

## Standardized Data Formats
The AI parsing enforces consistent formats for personnel data:
- **Education:** "Degree, Major, Institution (Year)" - one per line
- **Registrations:** "License Type #Number, State (Expiration)" - one per line
- **Training:** "Course Name (Year, Course Code)" - e.g., "Safety Inspection of In-Service Bridges (2001, NHI 130055)"
- **Other Qualifications:** Certifications, awards, publications - one per line

## Recent Changes
- Added personnel import from company websites (Jan 2026)
  - "Import from Website" button on Personnel page
  - Enter a team/about page URL to scrape personnel information
  - AI extracts name, title, role, education, registrations, and bio
  - Preview and select which personnel to import
  - Works with company about-us, team, and leadership pages
- Added data export/import functionality (Jan 2026)
  - Export all database records to JSON file from Settings page
  - Import data from JSON to restore or transfer between instances
  - Option to clear existing data before import or merge with existing
  - Handles ID remapping for foreign key relationships during import
- Added portfolio website scraping for project import (Jan 2026)
  - "From Website" tab in Import Projects modal
  - Enter portfolio page URL to scrape projects from company websites
  - Handles pagination and follows individual project links for details
  - AI extracts project title, location, client, year, cost, and description
  - Preview and select which projects to import
- Added multi-project import functionality (Jan 2026)
  - Parse multiple projects from a single document (like references tables or appendices)
  - "Import Projects" button on Projects page opens upload modal
  - AI extracts all projects with title, location, client, contacts, cost, year, description
  - Preview parsed projects with checkboxes to select which to import
  - Forced parsing option if auto-detection misclassifies document type
  - Batch save creates multiple project records at once
- Added AI project merge and SF330 inclusion flags for resume projects (Jan 2026)
  - Select 2+ projects on employee detail page, click "AI Merge Selected" to combine into one
  - Star icon on each project toggles SF330 inclusion flag for proposal recommendations
  - sf330_include field on EmployeeProjectExperience model
- Implemented Flask-Session with filesystem storage to fix session cookie size limit (Jan 2026)
  - Resume parsing now successfully extracts: name, title, years of experience (total and with firm), bio, education, PE/SE registrations, NHI training courses, and project experience
  - Session data stored in /tmp/flask_session instead of browser cookies to handle large parsed data (>4KB)
- Added Word document generation for SF330 forms (Jan 2026)
  - word_generator.py module fills Word templates with proposal data
  - Templates stored in templates/sf330_word/ for each section (A/C, E, F, G, H/I, Part II)
  - Section E generates one page per employee, Section F one per project
  - Downloads as ZIP file containing individual Word documents per section
  - Uses python-docx library for Word manipulation
- Added win theme and intelligence document uploads (Jan 2026)
  - win_theme field on Proposal for key messaging and strategy
  - ProposalIntelligence model stores competitor info, client background docs
  - Proposal wizard Step 1 has win theme textarea and intelligence upload section
  - Intelligence documents support descriptions and text extraction for AI use
- Added Marketing Photos section with tagging and filtering (Jan 2026)
  - MarketingPhoto model with caption and tags (comma-separated #tags)
  - ProposalSelectedMarketingPhoto junction table for proposal selections
  - Marketing photos page with upload, tag filtering, caption/tag editing
  - Proposal wizard Step 1 has tag filter buttons and photo selection grid
  - Multiple photos can be selected by clicking, stored with proposals
- Added firm photo upload and proposal selection (Jan 2026)
  - FirmPhoto model stores firm images in Object Storage
  - Photo gallery on firm edit page with upload, delete, set primary
  - ProposalSelectedFirmPhoto junction table links photos to proposals
  - Proposal wizard Step 1 shows firm photos when firm is selected
  - Click photos to toggle selection for inclusion in proposal
- Added previous proposal upload for AI reference (Jan 2026)
  - ProposalReference model stores uploaded PDF/Word documents with extracted text
  - Upload previous proposals in Step 1 or Step 4 of proposal wizard
  - Reference text included in AI cover letter generation for style/content matching
  - Download and delete reference documents from Step 4 review page
- Added photo upload for personnel and projects (Jan 2026)
  - EmployeePhoto and ProjectPhoto models store photo references with metadata
  - Photos stored in Replit Object Storage for long-term persistence
  - Photo gallery on employee and project detail pages
  - Upload with optional caption, delete functionality
  - Click to open full-size photo in new tab
- Added certification checklist for new personnel (Jan 2026)
  - CertificationType model stores master list of certification types
  - Add Personnel page shows checkboxes grouped by category (NHI, Safety, SPRAT, Drone, PE License)
  - Users can check certifications, details added later on certifications page
  - "Add New Certification Type" button adds new types to the master list dynamically
  - "Build Cert Checklist" button on Certifications page seeds types from existing data
- Added Certifications & Licenses management section (Jan 2026)
  - Certification model stores training, licenses, and certifications with PDF blob storage
  - Categories: NHI Training, Safety, SPRAT, Drone/FAA, PE Licenses by state
  - Import from License_Survey CSV to bulk create personnel and certifications
  - Click on certification to upload/view/delete PDF copies
  - Expiration tracking with status indicators (active, expired, registered)
  - Certifications page linked from navigation and employee detail page
- Added "Copy to Resume" feature on project detail page (Jan 2026)
  - Select project description version (main or any alternate) to copy
  - Multi-select employees to copy the project to their resume experience
  - Avoids duplicates if project already exists on resume
- Added AI cover letter generator in proposal wizard Step 4 (Jan 2026)
  - Combines RFP requirements, firm bio, personnel, and project data
  - Custom instructions popup for additional guidance
  - Cover letter and written sections stored on proposal
- Added RFP/RFQ document storage on proposals (Jan 2026)
  - Upload RFP file in Step 1, stored as binary (rfp_content) and extracted text (rfp_text)
  - RFP download link shown in Step 4 review page
- Added firm bio/writeup with alternate versions (Jan 2026)
  - Firms have bio text field for company writeup
  - FirmAlternateDescription model for version-specific bios
  - Proposals can select which firm bio version to use
- Enhanced employee project experience management (Jan 2026)
  - Alternate descriptions for resume projects with ExperienceAlternateDescription model
  - Project title autocomplete searches main Projects database and auto-fills location, year, cost, owner
  - Owner/client autocomplete connected to Client Contacts database
  - AI rewrite button with custom instructions popup for descriptions
  - "Copy to Other Resumes" - copy project experience to other employees
  - "Add to Projects Database" - promote resume project to main Projects database
- Added website scraping for firm information import (Jan 2026)
  - "Import from Website" section on Add Firm page
  - Enter a firm's website URL to automatically extract company information
  - AI parses website content and populates form fields (name, address, contact, etc.)
  - Populated fields are highlighted for easy review before saving
- Added proposal tracking numbers with search/filter functionality (Jan 2026)
  - Proposals now require a tracking_number field for unique identification
  - Proposals list page has search box (searches tracking #, name, title, solicitation #)
  - Status filter dropdown to show only draft or finalized proposals
  - Tracking number displayed prominently in proposals table
- Added Client Contacts database with autocomplete in project page (Jan 2026)
  - ClientContact model stores name, agency, role, phone, email, physical/mailing addresses
  - Contacts page for managing client contacts (CRUD)
  - Project page has autocomplete for owner contact - typing searches contacts
  - Selecting a contact auto-fills owner name and phone fields
- Added AI Settings admin page and custom rewrite instructions popup (Jan 2026)
  - Settings page (gear icon in nav) for global AI writing style and tone preferences
  - AISettings model stores key-value preferences in database
  - AI rewrite button now shows popup for custom instructions per use
  - Global style/tone settings + custom instructions combined for rewrites
- Added multiple alternate Brief Descriptions per project (Jan 2026)
  - Projects can now have multiple versions of Brief Description (Section F, Block 24)
  - Each alternate has a label and description text
  - AI rewrite button rewrites descriptions in structural engineer bridge inspection tone
  - Proposal wizard Step 3 allows selecting which description version to use per project
- Added merge and delete functionality for existing database records (Jan 2026)
  - Multi-select checkboxes on Personnel and Projects pages
  - "Merge Selected" button appears when 2+ items are selected
  - Merge page shows side-by-side comparison with field selection
  - AI "Combine" option for text fields
  - Delete buttons with confirmation dialogs
- Added duplicate employee detection and merge functionality (Jan 2026)
  - When uploading a resume for someone already in the database, system detects the duplicate by name
  - Side-by-side comparison page shows existing vs new data for each field
  - User can select which version to keep for each field
  - AI "Combine & Rewrite" feature merges text fields in professional structural engineering tone
  - New project experience is deduplicated by title/owner/firm before adding
- Added EmployeeProjectExperience model to track project history from resumes (Jan 2026)
  - AI resume parsing now extracts detailed project experience with title, location, cost, owner, role, and firm
  - Employee detail page shows and manages project experience with add/edit/delete functionality
  - Project experience included in Section E (Block 19) of generated PDFs
- Added RFP/RFQ upload parsing in proposal wizard Step 1 to auto-fill contract information (Jan 2026)
- Added standardized formatting for education, registrations, training, and qualifications (Jan 2026)
- Added separate "Training" field to store NHI courses, FHWA training, certifications
- Initial MVP implementation (Jan 2026)
