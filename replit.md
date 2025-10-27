# Overview
This project is a comprehensive Flask-based construction site visit tracking system. It aims to streamline site management, improve communication, and ensure efficient documentation and oversight within the construction industry. Key capabilities include advanced project management, robust user authentication, visit scheduling, professional report generation with photo annotation, approval workflows, and expense tracking. The system provides complete oversight for construction projects, with market potential in civil engineering and facade specialization.

# User Preferences
Preferred communication style: Simple, everyday language.
Mobile-first design: Date field should be the first input field in report forms.
Report forms: Location section removed from report creation/editing interface (geolocation remains active for visits and notifications).

# System Architecture

## Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM for database interactions.
- **Database**: Railway PostgreSQL for production, SQLite for development.
- **Authentication**: Flask-Login for session management and role-based access (regular/master users).
- **Forms**: WTForms for secure form handling and CSRF protection.
- **File Handling**: Manages file uploads (photos, documents) with a 16MB limit, supporting binary image storage in the database with filesystem fallback.
- **PDF Generation**: WeasyPrint for pixel-perfect HTML/CSS templates and ReportLab (legacy) for specific formats.
- **Geolocation**: Robust system with IP fallback and reverse geocoding using `geopy` for precise distance calculations.
- **CORS**: Flask-CORS configured with credentials support for API routes.
- **HTTPS Enforcement**: Automatic HTTPS redirect for production environments.

## Frontend Architecture
- **Templates**: Jinja2 templating engine, styled with Bootstrap 5.
- **Styling**: Custom CSS aligned with construction industry themes and ELP brand identity (dark gray, cyan).
- **JavaScript**: Vanilla JS for form validation, photo previews, and location services via Leaflet.js.
- **UI/UX**: Mobile-first design, PWA for installability and offline functionality, touch event optimization for photo editor on mobile. Dashboard features a clean, responsive grid layout for key statistics and recent reports.

## Data Model Design
- **Core Entities**: Users, Projects (with dynamic categories and configurable initial report numbering), Visits, Reports, Reimbursements, Checklist Templates, Communication Records, Notifications.
- **Projects (`Projeto`)**: Each project includes a `numeracao_inicial` field (default: 1) that defines the starting number for reports, enabling customized sequential numbering per project (e.g., start from report 100).
- **Photo Storage (`FotoRelatorio`)**: Stores binary image data, JSONB for annotation metadata, SHA-256 hash for deduplication, MIME type, and file size. Each photo now requires three mandatory fields displayed within its card: **Categoria** (project-specific category via dropdown), **Local** (location/area description, text up to 300 characters), and **Legenda** (caption - predefined or manual entry up to 500 characters).
- **Notifications (`Notificacao`)**: Internal notification system tracking report status changes with fields for origin/destination users, message content, type (e.g., enviado_para_aprovacao, aprovado), read status, and email delivery tracking.

## Key Features
- **Project Management**: CRUD operations, automatic numbering, GPS location, dynamic project categories with full lifecycle management (creation, editing, deletion, display) and project reactivation for master users. Each project allows configuring initial report numbering via the `numeracao_inicial` field.
- **Visit Tracking**: GPS-enabled logging, custom checklists, team communication.
- **Report System**: Professional PDF reports with photo annotation, ELP branding, and an approval workflow that includes automatic email notifications with PDF attachments to all relevant stakeholders (author, project manager, site staff, clients). Reports are numbered sequentially per project based on the project's configured initial numbering (numeracao_inicial + count). When creating reports from a pre-selected project, the Title and Project fields are hidden, showing only an informative blue card with project details.
- **Photo Management**: Advanced editing (drawing, arrows, text, captions), up to 50 photos per report, predefined caption management, deduplication via image hashing. Each image card displays three mandatory fields (**Categoria**, **Local**, **Legenda**) for inline editing without returning to the top of the page, enforced at form level, backend API, and frontend HTML validation.
- **Client Email Management**: CRUD system for client emails per project, including options for report reception.
- **Internal Notifications System**: Database-stored notifications with automatic email alerts for report status changes.
- **User Management**: Role-based access control.
- **Calendar System**: Visit scheduling, Google Calendar export.
- **Offline Functionality & PWA**: Full offline support, local storage, automatic sync.
- **Push Notifications**: Proximity alerts for sites, system updates, pending report notifications using geolocation.

## Security Implementation
- **CSRF Protection**: All forms include CSRF protection.
- **Authentication**: Session-based login with password hashing.
- **File Security**: Secure filename handling and file type validation.
- **Access Control**: Route protection based on login status and user roles, including specific permissions for master users on critical actions like project reactivation and report approval/deletion.

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
- **geopy**: Geocoding and precise distance calculations.