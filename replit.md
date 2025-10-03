# Overview
This project is a comprehensive construction site visit tracking system built with Flask, designed to streamline site management, improve communication, and ensure efficient documentation and oversight in the construction industry. It offers advanced project management, user authentication, visit scheduling, professional report generation with photo annotation, approval workflows, and expense tracking. The system aims to provide complete oversight for construction projects, with market potential in civil engineering and facade specialization.

## Recent Changes
- **Date**: October 3, 2025
- **Photo Upload System Overhaul**: Complete rewrite of image upload/storage/retrieval system
  - Added SHA-256 hash calculation for all uploaded images (64-character hex string)
  - Added content_type (MIME type) detection and storage for proper image serving
  - Added imagem_size field to track image file sizes
  - Implemented duplicate detection based on image hash to prevent redundant storage
  - Updated `/api/fotos/upload` endpoint with hash calculation, MIME detection, and metadata storage
  - Updated `/api/fotos/<foto_id>` endpoint to serve images with correct Content-Type headers
  - Added migration `20251003_0100` to add metadata fields to `fotos_relatorio` and `fotos_relatorios_express` tables
  - Filename now uses hash-based naming for consistency (`{hash}.{ext}`)
  - Cross-device compatibility ensured (Android, iOS, Desktop, APK)
  
- **Date**: October 2, 2025
- **Migration**: Updated `FotoRelatorio` model to use PostgreSQL JSONB for annotation data fields
  - Changed `anotacoes_dados` from Text to JSONB (db.JSON)
  - Changed `coordenadas_anotacao` from Text to JSONB (db.JSON)
  - Created migration script to clean invalid JSON data and convert field types
  - Updated routes.py to properly save Python objects (dict/list) instead of JSON strings
  - Fixed 4 locations in upload code that were incorrectly serializing JSON data
- **Image Storage**: Verified BYTEA storage and `/imagens/<id>` endpoint working correctly
- **Debug Enhancement (Oct 2, 2025)**:
  - Added comprehensive debug logging to image upload flow in routes.py (lines 1792-1827, 1978-1983)
  - Logs now track: photo_data keys, 'data' field presence, base64 preview, binary size, errors with traceback
  - Added post-commit verification to count photos with binary data saved
  - Confirmed database structure is correct (bytea field accepts binary data)
  - Created DIAGNOSTICO_IMAGENS.md with complete diagnostic information

# User Preferences
Preferred communication style: Simple, everyday language.
Mobile-first design: Date field should be the first input field in report forms.

# System Architecture

## Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM.
- **Database**: PostgreSQL for production, SQLite for development.
- **Authentication**: Flask-Login for session management and role-based access (regular/master users).
- **Forms**: WTForms for secure form handling and CSRF protection.
- **File Handling**: Manages file uploads (photos, documents) with a 16MB size limit, supporting binary image storage directly in the database with filesystem fallback.
- **PDF Generation**: Dual system with WeasyPrint (primary for pixel-perfect HTML/CSS templates) and ReportLab (legacy) for Artesano template format.
- **Geolocation**: Robust system with IP fallback, reverse geocoding, platform-specific instructions, and continuous monitoring.
- **CORS**: Flask-CORS configured with credentials support for API routes.
- **HTTPS Enforcement**: Automatic HTTPS redirect for production environments.

## Frontend Architecture
- **Templates**: Jinja2 templating engine, styled with Bootstrap 5.
- **Styling**: Custom CSS aligned with construction industry themes and ELP brand identity (dark gray, cyan).
- **JavaScript**: Vanilla JS for form validation, photo previews, and location services via Leaflet.js.
- **UI/UX**: Mobile-first design, PWA for installability and offline functionality, touch event optimization for photo editor on mobile.

## Data Model Design
- **Users**: Authentication, roles, contact info, project assignments.
- **Projects**: Sequential numbering (per-project), status tracking, categories, GPS coordinates.
- **Visits**: Scheduling, GPS logging, customizable checklist templates, status workflows.
- **Reports**: Document generation with photos, email distribution.
- **Reimbursements**: Expense tracking with categories and approval workflow.
- **Checklist Templates**: Defines `ChecklistTemplate` and `ChecklistItem`.
- **ComunicacaoVisita**: Model for visit-based communication.
- **FotoRelatorio**: Photo storage with BYTEA for binary data, JSONB for annotation metadata (`anotacoes_dados`, `coordenadas_anotacao`), SHA-256 hash for deduplication (`imagem_hash`), MIME type storage (`content_type`), and file size tracking (`imagem_size`).

## Key Features
- **Project Management**: CRUD operations, automatic numbering, GPS location.
- **Visit Tracking**: GPS-enabled logging, custom checklists, team communication.
- **Report System**: Professional PDF reports with photo annotation, ELP branding, and approval workflow.
- **Client Email Management**: CRUD system for client emails per project with duplicate prevention.
- **Photo Management**: Advanced photo editing (drawing, arrows, text, captions), support for up to 50 photos per report, and predefined caption management.
- **Communication System**: Visit-based messaging for collaboration.
- **Approval Workflow**: Admin approval for reports.
- **User Management**: Role-based access control.
- **Calendar System**: Visit scheduling, Google Calendar export, default checklist templates.
- **Offline Functionality & PWA**: Full offline support, local storage for form data, automatic sync, and PWA manifest.
- **Push Notifications**: Proximity alerts for sites, system updates, pending report notifications using geolocation, with dual location/notification permission flow.
- **Google Drive Integration**: Automatic backup of PDFs and images with project-specific folder organization.

## Security Implementation
- **CSRF Protection**: All forms include CSRF protection.
- **Authentication**: Session-based login with password hashing.
- **File Security**: Secure filename handling and file type validation.
- **Access Control**: Route protection based on login status and user roles.

# External Dependencies

## Core Flask Ecosystem
- **Flask-SQLAlchemy**: ORM for database interactions.
- **Flask-Login**: User session and authentication management.
- **Flask-Mail**: Email functionality.
- **Flask-WTF**: Form handling, CSRF protection, file uploads.
- **WTForms**: Form validation and rendering.
- **Flask-CORS**: Cross-Origin Resource Sharing management.

## Frontend Libraries
- **Bootstrap 5**: Responsive design framework.
- **Font Awesome 6**: Icon library.
- **Leaflet.js**: Interactive map selection.
- **JavaScript APIs**: Geolocation API, File API.

## Database Support
- **SQLite**: Development database.
- **PostgreSQL**: Production database.

## Email Integration
- **SMTP**: Configurable mail server (e.g., Gmail SMTP).

## PDF and Media Processing
- **WeasyPrint**: Primary PDF generation.
- **ReportLab**: Legacy PDF generation.
- **Pillow**: Image processing for annotations and resizing.
- **Canvas API**: JavaScript for photo annotation and drawing.

## Cloud Services
- **Google Drive API**: For automatic backups and file organization.
- **ipapi.co**: Geolocation fallback service.