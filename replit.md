# Overview

This is a comprehensive construction site visit tracking system built with Flask. The system provides advanced project management capabilities including user authentication, project creation, visit scheduling and communication, professional report generation with photo annotation tools, approval workflows, and expense tracking. Enhanced with PDF generation, photo editing capabilities, and admin approval processes for complete construction project oversight.

## Recent Changes (2025-08-18)
- Successfully migrated from Replit Agent to standard Replit environment
- Enhanced project creation form with text input for project type instead of dropdown selection
- Added GPS location capture functionality for project addresses
- Implemented interactive map selection for project locations using Leaflet.js
- Updated database schema to support GPS coordinates (latitude/longitude) for projects
- Configured PostgreSQL database for production use
- Fixed database schema issues by adding missing columns (latitude, longitude, tipo_obra)
- Application fully functional with admin user (admin/admin123)
- Project form now allows free text input for construction type and location selection via GPS or interactive map

### Latest Updates (Evening 2025-08-18)
- ✅ **Photo Editor Fixed**: Complete photo annotation system with drawing tools (pen, arrow, rectangle, circle, text)
- ✅ **Report System Functional**: Reports saving correctly with photos, fixed UI feedback issues
- ✅ **PDF Generation**: Professional PDF reports matching template format with photos and signatures
- ✅ **GPS Homepage**: Interactive map showing nearest construction sites based on user location
- ✅ **Database Configuration**: Upload folder configured, file handling improved
- ✅ **Complete Workflow**: Full report creation, editing, photo annotation, and PDF generation working

### Critical Fixes (2025-08-19 Morning)
- ✅ **50 Photo Limit**: Successfully increased from 5 to 50 photos per report in form_complete.html
- ✅ **GPS Address Formatting**: GPS now returns formatted addresses instead of raw coordinates
- ✅ **Dashboard Proximity**: Works showing projects ordered by distance with proper API endpoints
- ✅ **CSRF Issues Resolved**: API endpoints exempted from CSRF for proper functionality
- ✅ **Visual Indicators**: Added clear UI markers showing "50 fotos" and "NOVO" features

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
- **Visit Tracking**: GPS-enabled visit logging with customizable checklists and team communication
- **Enhanced Report System**: Professional PDF generation with photo annotation tools and approval workflows
- **Photo Management**: Advanced photo editing with drawing tools, arrows, text annotations, and captions
- **Communication System**: Visit-based messaging for team collaboration and progress tracking
- **Approval Workflow**: Admin approval process for reports before distribution
- **User Management**: Role-based access with master user privileges and approval authority
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

## PDF and Media Processing
- **ReportLab**: Professional PDF generation with custom styling and layouts
- **Pillow**: Image processing for photo annotations and resizing
- **Canvas API**: JavaScript-based photo annotation tools with drawing capabilities