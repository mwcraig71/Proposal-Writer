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

## Running the Application
The app runs on port 5000. Access via the webview.

## Standardized Data Formats
The AI parsing enforces consistent formats for personnel data:
- **Education:** "Degree, Major, Institution (Year)" - one per line
- **Registrations:** "License Type #Number, State (Expiration)" - one per line
- **Training:** "Course Name (Year, Course Code)" - e.g., "Safety Inspection of In-Service Bridges (2001, NHI 130055)"
- **Other Qualifications:** Certifications, awards, publications - one per line

## Recent Changes
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
