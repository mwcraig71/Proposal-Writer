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
- **Projects** - Example projects (Section F)
- **EmployeeProjectLink** - Many-to-many for Section G matrix
- **Proposals** - SF330 submission containers
- **ProposalSelectedEmployee/Project** - Junction tables

## Running the Application
The app runs on port 5000. Access via the webview.

## Standardized Data Formats
The AI parsing enforces consistent formats for personnel data:
- **Education:** "Degree, Major, Institution (Year)" - one per line
- **Registrations:** "License Type #Number, State (Expiration)" - one per line
- **Training:** "Course Name (Year, Course Code)" - e.g., "Safety Inspection of In-Service Bridges (2001, NHI 130055)"
- **Other Qualifications:** Certifications, awards, publications - one per line

## Recent Changes
- Added standardized formatting for education, registrations, training, and qualifications (Jan 2026)
- Added separate "Training" field to store NHI courses, FHWA training, certifications
- Initial MVP implementation (Jan 2026)
