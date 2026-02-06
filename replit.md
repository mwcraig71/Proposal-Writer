# SF330 AI Automation System

## Overview
This project is a Flask-based web application designed to automate the creation of Federal Standard Form 330 (SF330) Architect-Engineer Qualifications. It streamlines the proposal generation process for A/E firms by leveraging Google Gemini AI to parse documents, manage data, and build comprehensive proposals. The system aims to significantly reduce the manual effort and time required for SF330 submissions, enhancing efficiency and accuracy for AEC firms.

## User Preferences
The agent should prioritize iterative development and ask for confirmation before making major architectural changes or deleting significant portions of code. I prefer clear, concise explanations and well-documented code. Please use functional programming paradigms where appropriate and maintain a clean, modular codebase. Do not make changes to files in the `/orgchart` directory unless explicitly instructed, as this is a separate React application.

## System Architecture

### UI/UX Decisions
The frontend utilizes Jinja2 templates styled with Tailwind CSS for a responsive and modern user interface. The system features a wizard-style interface for proposal building, an interactive organizational chart builder using React/Vite with `@xyflow/react`, and customizable interfaces for data management. User interactions are designed to be intuitive, with features like drag-and-drop for staff assignment and visual feedback.

### Technical Implementations
The core application is built with Python Flask, employing SQLAlchemy ORM for database interactions. Google Gemini AI is integrated for document parsing and content generation, accessible via Replit AI Integrations.
- **AI-Powered Document Parsing:** Uploaded PDF/DOCX/XLSX files are processed by AI to extract structured data for resumes, project sheets, and firm profiles. This includes personnel details, project specifics, and certification records.
- **Data Management:** A robust system for CRUD operations on Firms, Employees, Projects, Client Contacts, Certifications, and Marketing Photos. Data is standardized for consistency.
- **Proposal Builder:** A multi-step wizard guides users through creating SF330 submissions, including selecting personnel, projects, and generating a Section G Matrix.
- **Organizational Chart Builder:** An interactive React/Vite application for dynamically creating and assigning roles within an organizational chart, with drag-and-drop functionality and auto-layout.
- **Content Generation:** AI assists in generating cover letters, rewriting descriptions (e.g., project descriptions, firm bios) with customizable instructions and style/tone preferences.
- **Document Generation:** The system can generate SF330 forms in both PDF and Word formats, filling templates with proposal data. Word generation creates individual documents per section, downloadable as a ZIP.
- **Import/Export Functionality:** Supports importing data from company websites (personnel, projects, firm info) and exporting/importing all database records as JSON for backup or migration.
- **Intelligent Features:** Includes duplicate detection for employees, project merging, tracking numbers for proposals, and management of win themes and intelligence documents for strategic proposal development.
- **Object Storage:** Photos for employees, projects, firms, and marketing assets are stored in Replit Object Storage.

### Feature Specifications
- **Document Upload & AI Parsing:** Handles various document types for data extraction.
- **Data Management:** Comprehensive CRUD for all entities (Firms, Employees, Projects, etc.). Projects are organized by firm with color-coded tabs for easy navigation. Firms support document storage (PDF, Word, Excel files) and Google Drive folder linking.
- **Hierarchical Project Structure:** Projects can be designated as "Contract Projects" (master level) or "Task Order Projects" (linked to a parent Contract). Task Orders are displayed nested below their parent Contract with visual indentation, amber indicators, and appropriate icons for quick identification. This supports complex multi-phase project tracking.
- **Contact Merge:** Duplicate client contacts can be merged by selecting multiple contacts, comparing fields side-by-side, and choosing which values to keep. The primary contact is preserved while others are deleted.
- **Project Download:** Projects can be downloaded as Word documents in three formats: (1) SF330 Section F template format with placeholder replacement; (2) Company Template format (customizable); (3) Plain Word format. All use `{{PLACEHOLDER}}` tags for data fields. Templates can be customized via Settings.
- **Resume Download:** Employee resumes can be downloaded as Word documents using a customizable template with `{{PLACEHOLDER}}` tags (EMPLOYEE_NAME, EMPLOYEE_TITLE, EMPLOYEE_ROLE, FIRM_NAME, EDUCATION, REGISTRATIONS, BIO, TRAINING, PROJECT_EXPERIENCE, etc.). Templates can be exported, customized, and re-imported via Settings.
- **Template Management:** Settings page provides export/import/reset for three template types: SF330 Section F, Company Project, and Resume. All use the same `{{PLACEHOLDER_NAME}}` syntax. Templates stored in Replit Object Storage.
- **Proposal Builder:** Multi-step wizard for SF330 creation with advanced selection and customization options.
- **Section G Matrix Auto-generation:** Automatically creates personnel-project participation grids.
- **PDF/Word Generation:** Fills SF330 templates with proposal-specific data.
- **Interactive Org Chart:** Visual assignment of personnel to roles with layout management.
- **Web Scraping:** Automated import of personnel, project, and firm information from URLs.
- **AI-powered Content Rewriting:** Customizable AI assistance for text generation and refinement.
- **Certification Management:** Tracking of employee certifications with expiration dates and PDF storage.
- **Proposal Intelligence:** Storage and utilization of RFP/RFQ documents, previous proposals, win themes, and competitor information for AI-assisted writing.
- **AI Proposal Assistant:** An integrated AI assistant on the proposal detail page that collects all proposal data (personnel, projects, firm info, org chart, RFP content, reference documents, intelligence files, performance references) and generates contextual responses. Uses intelligent chunked processing for large proposals—directly processing smaller proposals and summarizing sections for larger ones before generating final responses.
- **Performance References:** A dedicated section for storing client performance evaluations and testimonials. Supports manual entry or AI-powered PDF parsing to extract scores (0-10 scale), quotes, evaluator details, and project information from evaluation documents like SCDOT forms. References can be linked to proposals and appear on the proposal Step 4 page, providing the AI assistant with client feedback context for content generation. Features include filtering by client/firm/personnel, sorting by date/score, personnel tagging, and PDF upload with object storage for later download.

### System Design Choices
- **Modular Architecture:** The application is structured into logical modules (e.g., `routes.py`, `models.py`, `gemini_service.py`) for maintainability.
- **Database Schema:** Designed to support complex relationships between firms, employees, projects, proposals, and their associated details (e.g., `EmployeeProjectExperience`, `ProjectAlternateDescription`).
- **Session Management:** Utilizes Flask-Session with filesystem storage to handle large session data, addressing limitations of browser cookies.
- **Standardized Data Formats:** Enforces consistent data entry formats for qualifications like education, registrations, and training to optimize AI parsing and data integrity.

## External Dependencies
- **Google Gemini AI:** Used for intelligent document parsing, content generation, and text summarization.
- **PostgreSQL:** Relational database for persistent storage of all application data.
- **Tailwind CSS:** Utility-first CSS framework for styling the web application.
- **React/Vite:** Used for the interactive Organizational Chart module.
- **@xyflow/react and dagre:** Libraries used within the React Org Chart for node-based UI and graph layout.
- **python-docx:** Python library for generating and manipulating Word documents.