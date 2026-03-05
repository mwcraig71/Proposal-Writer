# SF330 AI Automation System

## Overview
This project is a Flask-based web application designed to automate the creation of Federal Standard Form 330 (SF330) Architect-Engineer Qualifications. It streamlines the proposal generation process for A/E firms by leveraging Google Gemini AI to parse documents, manage data, and build comprehensive proposals. The system aims to significantly reduce the manual effort and time required for SF330 submissions, enhancing efficiency and accuracy for AEC firms.

## User Preferences
The agent should prioritize iterative development and ask for confirmation before making major architectural changes or deleting significant portions of code. I prefer clear, concise explanations and well-documented code. Please use functional programming paradigms where appropriate and maintain a clean, modular codebase. Do not make changes to files in the `/orgchart` directory unless explicitly instructed, as this is a separate React application.

## System Architecture

### UI/UX Decisions
The frontend utilizes Jinja2 templates styled with Tailwind CSS for a responsive and modern user interface. The system features a wizard-style interface for proposal building, an interactive organizational chart builder using React/Vite with `@xyflow/react`, and customizable interfaces for data management. User interactions are designed to be intuitive, with features like drag-and-drop for staff assignment and visual feedback.

### Technical Implementations
The core application is built with Python Flask, employing SQLAlchemy ORM for database interactions. AI is integrated for document parsing and content generation via a centralized wrapper supporting multiple providers (Google Gemini and OpenAI) with user-selectable models.
- **AI-Powered Document Parsing:** Uploaded documents are processed by AI to extract structured data for resumes, project sheets, and firm profiles.
- **Data Management:** Robust CRUD operations for Firms, Employees, Projects, Client Contacts, Certifications, and Marketing Photos. Supports hierarchical project structures (Contract and Task Order Projects). Includes soft-delete for employees and projects, and a contact merge feature.
- **Proposal Builder:** A multi-step wizard for creating SF330 submissions, including personnel, projects, and Section G Matrix generation.
- **Organizational Chart Builder:** An interactive React/Vite application for dynamically creating and assigning roles, with drag-and-drop, various export options (PDF, JPG, SmartDraw CSV), and customizable visual settings. Supports multiple node types: CustomNode (standard roles), DisciplineBlockNode (dense blocks with lead + team list, firm abbreviations), SectionHeaderNode (wide colored banners for grouping), PICNode (Principal-in-Charge), and junction nodes. Features key individual star markers, firm abbreviation display, position persistence (manual positions preserved when adding nodes), and an enhanced legend showing firm logos, names, abbreviations, and key individual indicators.
- **Resume Graphic Builder:** An integrated React/Vite module for creating SF330 proposal graphics (Graphic Block Builder, Badge Builder, Key Staff listing), generating downloadable 300 DPI PNG images.
- **Content Generation:** AI assists in generating cover letters and rewriting descriptions with customizable instructions and style/tone preferences.
- **Document Generation:** Generates SF330 forms in PDF and Word formats. Supports customizable templates for SF330 Section F, Company Project, Resume, SF330 Section E Resume (with dynamic project block expansion), and SF330 Section G Matrix.
- **Import/Export Functionality:** Supports data import from company websites and JSON export/import for database records.
- **Intelligent Features:** Includes duplicate detection, project merging, proposal tracking numbers, and management of win themes and intelligence documents.
- **AI Project Experience Creation:** AI generates tailored project experience descriptions for employees based on firm projects, employee info, and selected roles.
- **Certification Management:** Tracks employee certifications with expiration dates and PDF storage.
- **Proposal Intelligence:** Stores and utilizes RFP/RFQ documents, previous proposals, win themes, and competitor information for AI-assisted writing.
- **AI Proposal Assistant:** An integrated AI assistant on the proposal detail page that collects all proposal data and generates contextual responses. Features a "Data Sources" picker with checkboxes and importance weights for selective AI context.
- **Proposal Review System:** AI-powered proposal review with three types: RFP Compliance Check, A&E Marketing Professional Review, and Senior Technical Engineer Review. Review prompts are customizable.
- **AI Writing Preferences:** Global settings for Writing Style, Writing Tone, Writing Sample (paste example text for AI to mimic), Banned Words/Phrases, Acronyms, and Industry Words/Phrases, injected into all AI prompts.
- **Multi-Address & Contact Management:** Firms support multiple addresses and contacts stored in `firm_addresses` and `firm_contacts` tables. Each entry has a label, full details, and a primary flag. When creating or editing a proposal, users can select which firm address and contact to use for that specific proposal (stored as `firm_address_id` and `firm_contact_id` on the proposal). The selected address/contact is used in SF330 Word document generation (Part II and signature). Falls back to the primary address/contact if none is selected.
- **Subconsultant Firms:** Allows adding subconsultant firms to proposals, with their data included as an AI data source.
- **Performance References:** Stores client performance evaluations, supporting manual entry or AI-powered PDF parsing. References can be linked to proposals, projects, and employees, providing AI context. Includes a feature to generate proposal-ready PNG images of notable quotes.

### System Design Choices
- **Modular Architecture:** Application structured into logical modules for maintainability.
- **Database Schema:** Designed to support complex relationships between entities.
- **Session Management:** Utilizes Flask-Session with filesystem storage for large session data.
- **Standardized Data Formats:** Enforces consistent data entry for qualifications.
- **Object Storage:** Photos and template files are stored in Replit Object Storage.

## External Dependencies
- **Google Gemini AI:** For intelligent document parsing, content generation, and text summarization.
- **PostgreSQL:** Relational database for persistent storage.
- **Tailwind CSS:** Utility-first CSS framework.
- **React/Vite:** For the interactive Organizational Chart and Resume Graphic Builder modules.
- **@xyflow/react and dagre:** Libraries for node-based UI and graph layout in the Org Chart.
- **python-docx:** Python library for generating and manipulating Word documents.