# Overview
This project is a comprehensive Flask-based construction site visit tracking system. It aims to streamline site management, improve communication, and ensure efficient documentation and oversight within the construction industry. Key capabilities include advanced project management, robust user authentication, visit scheduling, professional report generation with photo annotation, approval workflows, and expense tracking. The system provides complete oversight for construction projects, with market potential in civil engineering and facade specialization.

# User Preferences
Preferred communication style: Simple, everyday language.
Mobile-first design: Date field should be the first input field in report forms.
Report forms: Location section removed from report creation/editing interface (geolocation remains active for visits and notifications).

# Recent Changes

## November 2, 2025
- **Photo Upload Flexibility**: Removed mandatory validation for Categoria (category) and Local (location) fields in photo uploads. Users can now upload images directly from camera or gallery without being forced to fill in these fields, improving mobile UX and speed.
  - Modified `forms_express.py`: Changed validators from `DataRequired()` to `Optional()` for tipo_servico and local fields
  - Modified `routes.py`: Removed backend validation checks that rejected uploads with empty categoria or local
  - Legenda (caption) field remains mandatory as required
  - Changes apply to both frontend form validation and backend API validation

## October 31, 2025
- **Sistema de Notificações Web/Mobile Completo**: Implementado sistema completo de notificações internas com suporte a push notifications via Firebase Cloud Messaging, incluindo ícone de sino na navegação, painel lateral (drawer), API REST protegida, e limpeza automática de notificações expiradas.
- **Push Notifications**: Integrado Firebase FCM para envio de push notifications em eventos de aprovação e rejeição de relatórios. Requer configuração da variável de ambiente FIREBASE_CREDENTIALS_JSON.
- **Scheduler de Limpeza Automática**: Adicionado APScheduler com tarefas periódicas para remover notificações expiradas (>24h) automaticamente a cada 6 horas e diariamente às 3h da manhã.
- **Service Worker**: Configurado para receber e exibir push notifications com estratégia Network-First para garantir dados sempre atualizados do PostgreSQL.
- **Correções no Sistema de Notificações**: 
  - Adicionada notificação automática de "relatório pendente" quando relatórios são finalizados (status muda para "Aguardando Aprovação")
  - Corrigidos links de destino nas notificações para usar URLs corretos (/projects/{id}, /reports/{id}/review)
  - Implementada validação robusta de user_ids em criar_notificacao_obra_criada para prevenir IntegrityErrors quando projetos não têm responsável definido
  - Sistema agora trata corretamente obras sem responsáveis, registrando warning ao invés de falhar silenciosamente

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
- **Core Entities**: Users, Projects (with dynamic categories and configurable initial report numbering), Visits, Reports, Reimbursements, Checklist Templates, Communication Records, Notifications, Global and Temporary Approvers.
- **Projects (`Projeto`)**: Each project includes a `numeracao_inicial` field (default: 1) that defines the starting number for reports, enabling customized sequential numbering per project (e.g., start from report 100).
- **Reports (`Relatorio`)**: Includes `acompanhantes` field (JSONB) storing an array of visit attendees with structure: `[{"nome": "Name", "funcao": "Role", "origem": "Source"}]`. Supports both project employees and external attendees, fully backward compatible with existing reports. Also includes `lembrete_proxima_visita` (TEXT) field to store reminders for the next visit, displayed as a yellow warning card when creating new reports for the same project.
- **Photo Storage (`FotoRelatorio`)**: Stores binary image data, JSONB for annotation metadata, SHA-256 hash for deduplication, MIME type, and file size. Each photo displays three fields within its card: **Categoria** (project-specific category via dropdown, optional), **Local** (location/area description, text up to 300 characters, optional), and **Legenda** (caption - predefined or manual entry up to 500 characters, mandatory). Only the caption field is required for upload; category and location can be added later for better organization.
- **Notifications (`Notificacao`)**: Internal notification system tracking report status changes with fields for origin/destination users, message content, type (e.g., enviado_para_aprovacao, aprovado), read status, and email delivery tracking.
- **Aprovador Global (`AprovadorPadrao` with `is_global=True`)**: Single system-wide approver who can transfer their role and manage temporary approvers. Only one active global approver exists at any time. Has exclusive permissions to transfer the global approver role and manage temporary approvers - Master users cannot override these permissions.
- **Aprovadores Temporários (`AprovadorPadrao` with `is_global=False`)**: Project-specific approvers that override the global approver for particular projects. Can only be added, edited, or removed by the Aprovador Global.
- **Checklist Individual por Obra (`ChecklistObra`, `ProjetoChecklistConfig`)**: Each project can have a customized checklist based on the global template. Projects can add, edit, or remove items specific to their needs without affecting other projects. The checklist is displayed in a dedicated tab on the project view page with AJAX loading.

## Key Features
- **Project Management**: CRUD operations, automatic numbering, GPS location, dynamic project categories with full lifecycle management (creation, editing, deletion, display) and project reactivation for master users. Each project allows configuring initial report numbering via the `numeracao_inicial` field. **Checklist per Project**: Each project has a dedicated "Checklist da Obra" tab that displays the project's customized checklist items loaded via AJAX, with a button to access the full management interface for adding, editing, or removing items.
- **Visit Tracking**: GPS-enabled logging, custom checklists, team communication.
- **Report System**: Professional PDF reports with photo annotation, ELP branding, and an approval workflow that includes automatic email notifications with PDF attachments to all relevant stakeholders (author, project manager, site staff, clients). Reports are numbered sequentially per project based on the project's configured initial numbering (numeracao_inicial + count). When creating reports from a pre-selected project, the Title and Project fields are hidden, showing only an informative blue card with project details. **Reminder for Next Visit**: Each report can include a reminder for the next visit; when creating a new report for the same project, the previous reminder is displayed in a yellow warning card at the top of the form.
- **Photo Management**: Advanced editing (drawing, arrows, text, captions), up to 50 photos per report, predefined caption management, deduplication via image hashing. Each image card displays three fields (**Categoria**, **Local**, **Legenda**) for inline editing without returning to the top of the page. Only Legenda (caption) is mandatory; Categoria and Local are optional and can be filled later, improving mobile upload speed and UX.
- **Client Email Management**: CRUD system for client emails per project, including options for report reception.
- **Internal Notifications System**: Database-stored notifications with automatic email alerts for report status changes.
- **User Management**: Role-based access control.
- **Approval Management System**: 
  - **Aprovador Global**: Single system-wide approver with exclusive permissions to transfer their role and manage temporary approvers. Only the current Aprovador Global can perform these critical actions - even Master users cannot override this restriction. The system enforces strict permission controls ensuring only the Aprovador Global (identified by matching aprovador_global.aprovador_id) can transfer the global role or manage temporary approvers.
  - **Aprovadores Temporários**: Project-specific approvers that override the global approver for particular projects. Can only be added, edited, or removed by the Aprovador Global. Each project can have at most one temporary approver.
  - **Permission Enforcement**: Backend validation ensures security at the route level with strict checks using `current_user_is_aprovador_global()`, while frontend UI provides clear visual feedback (disabled buttons with tooltips) for users without appropriate permissions. All critical routes validate permissions before executing any actions.
  - **Exception Handling**: Master users can define the first Aprovador Global when none exists, after which all approver management becomes exclusive to the Aprovador Global. This is the only exception to the strict permission rules.
  - **CSRF Protection**: All forms related to approver management include CSRF tokens to prevent security vulnerabilities.
- **Calendar System**: Visit scheduling, Google Calendar export.
- **Offline Functionality & PWA**: Full offline support, local storage, automatic sync.
- **Push Notifications**: Proximity alerts for sites, system updates, pending report notifications using geolocation.

## Security Implementation
- **CSRF Protection**: All forms include CSRF protection via csrf_token() in templates.
- **Authentication**: Session-based login with password hashing.
- **File Security**: Secure filename handling and file type validation.
- **Access Control**: Route protection based on login status and user roles, including specific permissions for master users on critical actions like project reactivation and report approval/deletion.
- **Aprovador Global Permission System**: Strict permission controls ensuring only the Aprovador Global can transfer their role or manage temporary approvers. Backend routes validate permissions using `current_user_is_aprovador_global()` which checks if the current user's ID matches the stored global approver's ID. Master users can only define the first Aprovador Global when none exists; after that, all approver management is exclusive to the Aprovador Global. Frontend provides disabled buttons with tooltips for unauthorized users.

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