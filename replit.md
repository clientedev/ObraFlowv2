# Overview
This project is a comprehensive Flask-based construction site visit tracking system designed to streamline site management, improve communication, and ensure efficient documentation and oversight in the construction industry. It offers advanced project management, user authentication, visit scheduling, professional report generation with photo annotation, approval workflows, and expense tracking. The system aims to provide complete oversight for construction projects, with market potential in civil engineering and facade specialization.

# User Preferences
Preferred communication style: Simple, everyday language.
Mobile-first design: Date field should be the first input field in report forms.
Report forms: Location section removed from report creation/editing interface (geolocation remains active for visits and notifications).

# System Architecture

## Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM.
- **Database**: Railway PostgreSQL (production), configured via DATABASE_URL environment variable. SQLite for development.
- **Authentication**: Flask-Login for session management and role-based access (regular/master users).
- **Forms**: WTForms for secure form handling and CSRF protection.
- **File Handling**: Manages file uploads (photos, documents) with a 16MB size limit, supporting binary image storage directly in the database with filesystem fallback.
- **PDF Generation**: Dual system with WeasyPrint (primary for pixel-perfect HTML/CSS templates) and ReportLab (legacy) for Artesano template format.
- **Geolocation**: Robust system with IP fallback, reverse geocoding, platform-specific instructions.
- **CORS**: Flask-CORS configured with credentials support for API routes.
- **HTTPS Enforcement**: Automatic HTTPS redirect for production environments.

## Frontend Architecture
- **Templates**: Jinja2 templating engine, styled with Bootstrap 5.
- **Styling**: Custom CSS aligned with construction industry themes and ELP brand identity (dark gray, cyan).
- **JavaScript**: Vanilla JS for form validation, photo previews, and location services via Leaflet.js.
- **UI/UX**: Mobile-first design, PWA for installability and offline functionality, touch event optimization for photo editor on mobile.

## Data Model Design
- **Core Entities**: Users, Projects (with dynamic categories), Visits, Reports, Reimbursements, Checklist Templates, Communication Records.
- **Photo Storage (`FotoRelatorio`)**: BYTEA for binary image data, JSONB for annotation metadata (`anotacoes_dados`, `coordenadas_anotacao`), SHA-256 hash for deduplication (`imagem_hash`), MIME type storage (`content_type`), and file size tracking (`imagem_size`).

## Key Features
- **Project Management**: CRUD operations, automatic numbering, GPS location, dynamic project categories.
- **Visit Tracking**: GPS-enabled logging, custom checklists, team communication.
- **Report System**: Professional PDF reports with photo annotation, ELP branding, and approval workflow.
- **Photo Management**: Advanced editing (drawing, arrows, text, captions), up to 50 photos per report, predefined caption management, deduplication via image hashing.
- **Client Email Management**: CRUD system for client emails per project.
- **Approval Workflow**: Admin approval for reports.
- **User Management**: Role-based access control.
- **Calendar System**: Visit scheduling, Google Calendar export.
- **Offline Functionality & PWA**: Full offline support, local storage, automatic sync.
- **Push Notifications**: Proximity alerts for sites, system updates, pending report notifications using geolocation.
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
- **Flask-CORS**: Cross-Origin Resource Sharing management.

## Frontend Libraries
- **Bootstrap 5**: Responsive design framework.
- **Font Awesome 6**: Icon library.
- **Leaflet.js**: Interactive map selection.

## Database Support
- **PostgreSQL**: Production database.
- **SQLite**: Development database.

## Email Integration
- **SMTP**: Configurable mail server.

## PDF and Media Processing
- **WeasyPrint**: Primary PDF generation.
- **ReportLab**: Legacy PDF generation.
- **Pillow**: Image processing for annotations and resizing.
- **Canvas API**: JavaScript for photo annotation and drawing.

## Cloud Services
- **Google Drive API**: For automatic backups and file organization.
- **ipapi.co**: Geolocation fallback service.