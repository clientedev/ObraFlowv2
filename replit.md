# Overview

This is a construction site visit tracking system built with Flask. It's designed to help construction companies manage projects, schedule and track visits, create reports, and handle reimbursements. The system provides a complete workflow for construction project management including user authentication, project creation, visit scheduling, report generation with photos, and expense tracking.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM for database operations
- **Database**: SQLite for development with PostgreSQL support configured via environment variables
- **Authentication**: Flask-Login for session management with role-based access (regular users vs master users)
- **Forms**: WTForms with CSRF protection for secure form handling
- **File Handling**: File upload system for photos and documents with size limits (16MB max)

## Frontend Architecture
- **Templates**: Jinja2 templating engine with Bootstrap 5 for responsive UI
- **Styling**: Custom CSS with construction industry color themes (orange, yellow, blue)
- **JavaScript**: Vanilla JavaScript for form validation, photo preview, and location services
- **Components**: Modular template structure with base template and specialized forms

## Data Model Design
- **Users**: Authentication with roles (master/regular), contact information, and project assignments
- **Projects**: Sequential numbering system, status tracking, and type categorization
- **Visits**: Scheduling system with GPS coordinates, checklist templates, and status workflow
- **Reports**: Document generation with photo attachments and email distribution
- **Reimbursements**: Expense tracking with categorized costs and approval workflow

## Key Features
- **Project Management**: CRUD operations with automatic numbering (PROJ-0001 format)
- **Visit Tracking**: GPS-enabled visit logging with customizable checklists
- **Report System**: Structured reports with photo uploads and email functionality
- **User Management**: Role-based access with master user privileges
- **File Management**: Secure file uploads with proper validation and storage

## Security Implementation
- **CSRF Protection**: All forms protected against cross-site request forgery
- **Authentication**: Session-based login with password hashing
- **File Security**: Secure filename handling and file type validation
- **Access Control**: Route protection with login requirements and role checks

# External Dependencies

## Core Flask Ecosystem
- **Flask-SQLAlchemy**: Database ORM for model definitions and queries
- **Flask-Login**: User session management and authentication
- **Flask-Mail**: Email functionality for report distribution
- **Flask-WTF**: Form handling with CSRF protection and file uploads
- **WTForms**: Form validation and rendering

## Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive design and components
- **Font Awesome 6**: Icon library for consistent UI elements
- **JavaScript APIs**: Geolocation API for GPS coordinates, File API for photo handling

## Database Support
- **SQLite**: Default development database
- **PostgreSQL**: Production database support via DATABASE_URL environment variable

## Email Integration
- **SMTP**: Configurable mail server (defaults to Gmail SMTP)
- **Environment Variables**: MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD for email configuration

## Development Tools
- **Werkzeug**: WSGI utilities including ProxyFix for deployment
- **Python Logging**: Debug logging configuration for development