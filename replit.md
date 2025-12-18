# Overview
This project is a comprehensive Flask-based construction site visit tracking system designed to streamline site management, improve communication, and ensure efficient documentation and oversight within the construction industry. It offers advanced project management, robust user authentication, visit scheduling, professional report generation with photo annotation, approval workflows, expense tracking, autosave functionality with real-time synchronization, and a comprehensive notification system. The system provides complete oversight for construction projects, with market potential in civil engineering and facade specialization.

# User Preferences
Preferred communication style: Simple, everyday language.
Mobile-first design: Date field should be the first input field in report forms.
Report forms: Location section removed from report creation/editing interface (geolocation remains active for visits and notifications).

# System Architecture

## Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM.
- **Database**: Railway PostgreSQL for production, SQLite for development.
- **Authentication**: Flask-Login for session management and role-based access (regular/master users).
- **Forms**: WTForms for secure form handling and CSRF protection.
- **File Handling**: Manages file uploads (photos, documents) with a 50MB limit per file, supporting binary image storage in the database with filesystem fallback.
- **PDF Generation**: WeasyPrint for pixel-perfect HTML/CSS templates.
- **Geolocation**: Robust system with IP fallback and reverse geocoding using `geopy`.
- **CORS**: Flask-CORS configured with credentials support.
- **HTTPS Enforcement**: Automatic HTTPS redirect for production.
- **Notifications**: Internal notification system with Firebase Cloud Messaging (FCM) push notifications and APScheduler for cleanup.

## Frontend Architecture
- **Templates**: Jinja2 templating engine, styled with Bootstrap 5.
- **Styling**: Custom CSS aligned with construction industry themes (dark gray, cyan).
- **JavaScript**: Vanilla JS for form validation, photo previews, and location services via Leaflet.js.
- **UI/UX**: Mobile-first design, PWA for installability and offline functionality, touch event optimization for photo editor. Dashboard features a responsive grid layout.

## Data Model Design
- **Core Entities**: Users, Projects, Visits, Reports, Reimbursements, Checklist Templates, Communications, Notifications, Global and Temporary Approvers, Express Reports.
- **Projects**: Includes `numeracao_inicial` for custom sequential report numbering. Tabbed listing for "Ativas", "Não iniciadas", "Pausadas", "Concluídas". Distance-based sorting using Haversine formula.
- **Reports**: Includes `acompanhantes` (JSONB), `lembrete_proxima_visita` (TIMESTAMP), `categoria`, `local`, `observacoes_finais` (TEXT), `criado_por`, and `atualizado_por`.
- **Express Reports**: New independent report type not requiring pre-registered projects, with inline project/obra fields.
- **Photo Storage**: Stores binary image data, JSONB for annotation metadata, SHA-256 hash for deduplication. Each photo card displays optional **Categoria**, optional **Local**, and mandatory **Legenda**. `FotoRelatorio` includes `url`, `legenda` (TEXT), `ordem` (INTEGER).
- **Notifications**: Tracks report status changes, origin/destination users, message content, type, read status, and email delivery.
- **Aprovador Global**: Single system-wide approver with exclusive permissions.
- **Aprovadores Temporários**: Project-specific approvers, managed by the Aprovador Global, with multi-project selection.
- **Checklist Individual por Obra**: Customizable checklists per project based on a global template. UI improvements hide observation textareas for unchecked items.

## Key Features
- **Project Management**: CRUD operations, automatic numbering, GPS location, dynamic categories, project reactivation, and project-specific checklists.
- **Visit Tracking**: GPS-enabled logging, custom checklists, team communication.
- **Report System**: Professional PDF reports with photo annotation, ELP branding, and an approval workflow with email notifications. Reports are numbered sequentially per project. Reminders for next visits are displayed. Autosave system with 2s debounce, automatic persistence of all fields, and temporary image uploads.
- **Photo Management**: Advanced editing (drawing, arrows, text, captions), up to 50 photos per report, predefined caption management, deduplication. Drag-and-drop reordering, real-time synchronization, 50MB file size limit per image.
- **REST API**: Complete RESTful API for reports with POST/GET/PUT/DELETE endpoints, atomic transactions, and validation. Autosave endpoint (`/api/relatorios/autosave`) processes partial updates and temporary image uploads.
- **Client Email Management**: CRUD system for client emails per project.
- **Internal Notifications System**: Database-stored notifications with automatic email alerts and push notifications.
- **User Management**: Role-based access control.
- **Approval Management System**: Global and temporary approvers with strict permission enforcement and CSRF protection.
- **Calendar System**: Visit scheduling, Google Calendar export with multi-select and re-export functionality.
- **Offline Functionality & PWA**: Full offline support, local storage, automatic sync.
- **Push Notifications**: Proximity alerts, system updates, pending report notifications.

## Security Implementation
- **CSRF Protection**: All forms include CSRF protection.
- **Authentication**: Session-based login with password hashing.
- **File Security**: Secure filename handling and file type validation.
- **Access Control**: Route protection based on login status and user roles. Centralized `can_edit_report()` helper function.
- **Aprovador Global Permission System**: Strict permission controls for global and temporary approver management.

# Recent Changes (Dezembro 2025)

## Implementação de Envio de E-mails (18/12/2025)
- **Novo arquivo**: `email_service_smtp.py` - Serviço SMTP para aprovação de relatórios
- **Rotas atualizadas**: 
  - `/reports/<id>/approve` (linha 3922)
  - `/reports/<report_id>/approve` (linha 7555)
- **Funcionalidade**: Envio automático de e-mails quando um relatório é aprovado
- **Destinatários automáticos**:
  - Autor do relatório
  - Aprovador global
  - Todos os acompanhantes da visita
  - Responsável da obra
- **Conteúdo**: Template padronizado com nome, obra, data de aprovação
- **Anexo**: PDF do relatório gerado automaticamente
- **Tratamento de erros**: E-mails inválidos não quebram o fluxo de aprovação

# External Dependencies

## Core Flask Ecosystem
- **Flask-SQLAlchemy**: ORM.
- **Flask-Login**: User session and authentication.
- **Flask-Mail**: Email functionality.
- **Flask-WTF**: Form handling, CSRF protection, file uploads.
- **Flask-CORS**: Cross-Origin Resource Sharing.

## Frontend Libraries
- **Bootstrap 5**: Responsive design framework.
- **Font Awesome 6**: Icon library.
- **Leaflet.js**: Interactive map selection.

## Database Support
- **PostgreSQL**: Production database.
- **SQLite**: Development database.

## Email Integration (Aprovação de Relatórios)
- **SMTP**: Gmail SMTP (smtp.gmail.com:587)
- **Credenciais**: relatorios@elpconsultoria.eng.br / 1234567890 (hardcoded conforme especificação)
- **Disparo**: Automático ao aprovar relatório (normal ou express)
- **Destinatários**: Autor, aprovador, acompanhantes e responsável da obra
- **Anexo**: PDF do relatório aprovado
- **Implementação**: `email_service_smtp.py` com tratamento robusto de erros

## PDF and Media Processing
- **WeasyPrint**: Primary PDF generation.
- **Pillow**: Image processing.
- **Canvas API**: JavaScript for photo annotation.

## Cloud Services
- **Firebase Cloud Messaging (FCM)**: Push notifications.
- **Google Drive API**: Automatic backups.
- **ipapi.co**: Geolocation fallback.
- **geopy**: Geocoding and precise distance calculations.