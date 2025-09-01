# Overview
This project is a comprehensive construction site visit tracking system built with Flask, providing advanced project management capabilities. It includes user authentication, project creation, visit scheduling and communication, professional report generation with photo annotation tools, approval workflows, and expense tracking. The system is enhanced with PDF generation, advanced photo editing, and robust admin approval processes, aiming to provide complete oversight for construction projects. The business vision is to streamline site management, improve communication, and ensure efficient documentation and oversight in the construction industry, with market potential in civil engineering and facade specialization.

# User Preferences
Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **Framework**: Flask web framework utilizing SQLAlchemy ORM for database interactions.
- **Database**: Configured for PostgreSQL in production environments, with SQLite for development.
- **Authentication**: Flask-Login handles user session management, supporting role-based access for regular and master users.
- **Forms**: WTForms provides secure form handling with integrated CSRF protection.
- **File Handling**: Manages file uploads, including photos and documents, with defined size limits (16MB max).

## Frontend Architecture
- **Templates**: Jinja2 templating engine is used, styled with Bootstrap 5 for responsive UI.
- **Styling**: Features custom CSS aligned with construction industry color themes and ELP brand identity (dark gray, cyan).
- **JavaScript**: Employs vanilla JavaScript for functionalities such as form validation, photo previews, and location services (including interactive map selection via Leaflet.js).
- **Components**: Utilizes a modular template structure for maintainability.

## Data Model Design
- **Users**: Manages authentication, roles (master/regular), contact information, and project assignments.
- **Projects**: Implements a sequential numbering system, tracks status, and categorizes project types, including GPS coordinates (latitude/longitude).
- **Visits**: Supports scheduling with GPS logging, customizable checklist templates, and status workflows.
- **Reports**: Facilitates document generation with attached photos and supports email distribution.
- **Reimbursements**: Tracks expenses with categorized costs and an approval workflow.
- **Checklist Templates**: Defines `ChecklistTemplate` and `ChecklistItem` models for customizable checklists.
- **ComunicacaoVisita**: Model for visit-based communication.

## Key Features
- **Project Management**: Provides CRUD operations for projects, including automatic numbering and GPS location capture.
- **Visit Tracking**: Enables GPS-enabled visit logging, custom checklists, and team communication.
- **Enhanced Report System**: Generates professional PDF reports with integrated photo annotation tools and an approval workflow, complete with ELP branding.
- **Professional PDF Generation**: Dual PDF generation system with WeasyPrint (primary) for pixel-perfect HTML/CSS template replication and ReportLab (legacy) backup, following exact Artesano template format with company branding, dynamic data population, and responsive design for browser/download options.
- **Client Email Management**: Complete CRUD system for managing client emails per project with mandatory primary email, duplicate prevention, and administrative panel.
- **Photo Management**: Offers advanced photo editing capabilities including drawing tools, arrows, text annotations, and captions, supporting up to 50 photos per report.
- **Communication System**: Incorporates visit-based messaging for team collaboration and progress tracking.
- **Approval Workflow**: Implements an admin approval process for reports.
- **User Management**: Supports role-based access control.
- **File Management**: Ensures secure file uploads with validation and storage.
- **Calendar System**: Allows visit scheduling, Google Calendar export, and manages default checklist templates.
- **Offline Functionality & PWA**: Features full offline support via Service Worker, local storage for form data, automatic sync, and a Progressive Web App (PWA) manifest for installability and native app experience.
- **Push Notifications**: Provides proximity alerts for nearby construction sites (500m radius), system updates, and pending report notifications for administrators, leveraging geolocation monitoring.
- **Google Drive Backup**: Automated cloud backup system with OAuth 2.0 authentication, automatic project folder organization, comprehensive file management for PDFs and images, manual backup triggers, and cross-device compatibility.

## Security Implementation
- **CSRF Protection**: All forms are protected against cross-site request forgery.
- **Authentication**: Session-based login with password hashing.
- **File Security**: Ensures secure filename handling and file type validation.
- **Access Control**: Implements route protection based on login status and user roles.

# External Dependencies

## Core Flask Ecosystem
- **Flask-SQLAlchemy**: ORM for database interactions.
- **Flask-Login**: Manages user sessions and authentication.
- **Flask-Mail**: Facilitates email functionality.
- **Flask-WTF**: Handles forms, CSRF protection, and file uploads.
- **WTForms**: Provides form validation and rendering capabilities.

## Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive design.
- **Font Awesome 6**: Icon library for UI elements.
- **Leaflet.js**: Used for interactive map selection for project locations.
- **JavaScript APIs**: Utilizes Geolocation API for GPS coordinates and File API for photo handling.

## Database Support
- **SQLite**: Primarily used for development.
- **PostgreSQL**: Configured for production environments via `DATABASE_URL`.

## Email Integration
- **SMTP**: Configurable mail server, defaulting to Gmail SMTP, with settings managed via environment variables (`MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD`).

## PDF and Media Processing
- **WeasyPrint**: Primary PDF generation engine using HTML/CSS templates for pixel-perfect visual fidelity and exact template replication.
- **ReportLab**: Legacy PDF generation system maintained for backward compatibility.
- **Pillow**: Used for image processing, including photo annotations and resizing.
- **Canvas API**: JavaScript-based tool for photo annotation and drawing.

### WeasyPrint PDF System Implementation (2025-08-30)
- ✅ **Complete HTML/CSS Template System**: Professional template matching exact Artesano visual specifications
- ✅ **Dual Generator Architecture**: WeasyPrint primary, ReportLab legacy fallback
- ✅ **Pixel-Perfect Rendering**: Exact font sizes, colors, spacing, and layout compliance
- ✅ **Dynamic Data Integration**: JSON-based data population with Jinja2 templating
- ✅ **Photo Embedding**: Base64 image embedding for self-contained PDFs
- ✅ **Professional Styling**: Arial/Helvetica fonts, precise margins, header/footer positioning

### Predefined Caption Management System (2025-08-30)
- ✅ **Developer User Type**: Exclusive access with login "Desenvolvedor" / password "sen@i103"
- ✅ **Caption Database Model**: LegendaPredefinida with categories, status control, and audit trail
- ✅ **Administrative Interface**: Full CRUD operations with responsive design and category filtering
- ✅ **Photo Editor Integration**: Real-time caption loading with category filters in photo annotation tool
- ✅ **API Endpoint**: /api/legendas for dynamic caption retrieval by category
- ✅ **Multi-Category Support**: 8 specialized categories (Geral, Estrutural, Hidráulica, Elétrica, Acabamentos, Segurança, Fachada, Impermeabilização)
- ✅ **Dual Caption Mode**: Users can select predefined captions or write custom ones

### Google Drive Backup System (2025-09-01)
- ✅ **OAuth 2.0 Integration**: Secure authentication with Google Drive API using environment variables
- ✅ **Automatic Project Folders**: Creates organized folders by project number and name in shared Drive folder
- ✅ **Comprehensive File Support**: Backs up PDF reports, Express reports, and all attached photos
- ✅ **Automatic Triggers**: Executes backup whenever reports are created or finalized
- ✅ **Manual Backup**: One-click backup button available on project details page
- ✅ **Admin Interface**: Configuration page for setting up and monitoring backup status
- ✅ **Error Handling**: Robust error reporting and recovery mechanisms
- ✅ **Cross-Platform**: Works on desktop, tablet, and mobile devices
- ✅ **Security**: Uses secure credential storage via Replit environment variables
- ✅ **Shared Folder Integration**: Links to predefined Google Drive shared folder (ID: 1DasfSDL0832tx6AQcQGMFMlOm4JMboAx)

### Mobile Photo Editor Enhancement (2025-08-20)
- ✅ **Touch Events Optimization**: Melhorado manuseio de eventos touch para ferramentas além do pincel
- ✅ **Gesture Prevention**: Prevenção de zoom e gestos indesejados durante edição
- ✅ **Coordinate Mapping**: Correção do mapeamento de coordenadas touch para canvas
- ✅ **Mobile CSS**: Estilos otimizados com áreas de toque maiores e responsividade
- ✅ **Tool Preview**: Sistema de preview em tempo real para setas, círculos e retângulos
- ✅ **iOS Compatibility**: Otimizações específicas para Safari iOS e prevenção de zoom duplo-toque
