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
- **Data Management:** Comprehensive CRUD for all entities (Firms, Employees, Projects, etc.).
- **Proposal Builder:** Multi-step wizard for SF330 creation with advanced selection and customization options.
- **Section G Matrix Auto-generation:** Automatically creates personnel-project participation grids.
- **PDF/Word Generation:** Fills SF330 templates with proposal-specific data.
- **Interactive Org Chart:** Visual assignment of personnel to roles with layout management.
- **Web Scraping:** Automated import of personnel, project, and firm information from URLs.
- **AI-powered Content Rewriting:** Customizable AI assistance for text generation and refinement.
- **Certification Management:** Tracking of employee certifications with expiration dates and PDF storage.
- **Proposal Intelligence:** Storage and utilization of RFP/RFQ documents, previous proposals, win themes, and competitor information for AI-assisted writing.

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