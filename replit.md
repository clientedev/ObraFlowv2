# Overview
This project is a comprehensive Flask-based construction site visit tracking system designed to streamline site management, improve communication, and ensure efficient documentation and oversight within the construction industry. It offers advanced project management, robust user authentication, visit scheduling, professional report generation with photo annotation, approval workflows, expense tracking, autosave functionality with real-time synchronization, and a comprehensive notification system. The system provides complete oversight for construction projects, with market potential in civil engineering and facade specialization.

# Recent Changes
**December 16, 2025** - Express Report (Relatório Express) Feature:
- Implemented new independent report type that doesn't require pre-registered projects
- Express Reports include inline project/obra fields: nome, endereço, tipo, construtora, responsável, email, telefone
- Same status flow as Common Report: Em preenchimento → Aguardando Aprovação → Aprovado/Rejeitado
- New database models: RelatorioExpress and FotoRelatorioExpress in models.py
- New routes in routes_express.py with complete CRUD operations (create, read, update, delete)
- Templates: express_form.html, express_list.html, express_view.html
- Navigation menu updated with "Relatório Express" and "Listar Express" links
- Support for checklist, photos, acompanhantes, and all standard report fields
- Full approval workflow with approve/reject actions and comments

**December 16, 2025** - PDF Report Generation Adjustments:
- Increased logo size in PDF header from 150x55px to 200x75px
- Fixed date/time display to use report creation date (data_relatorio) instead of PDF generation time
- Fixed company field to use projeto.construtora instead of projeto.nome
- Enhanced photo captions to include category (tipo_servico) and location (local) metadata
- Fixed "Responsável pelo acompanhamento" field to show all participant names from acompanhantes JSONB array
- Fixed signatures section positioning: appears on first page when 0-2 photos, moves to last photo page when more photos

**December 15, 2025** - Melhorias na interface de obras:
- Listagem de obras (/projects) agora tem 4 abas: Ativas, Não iniciadas, Pausadas, Concluídas
- Tela da obra (/projects/{id}) recebeu menu hambúrguer ao lado do nome com acesso rápido às seções
- Lógica de redirecionamento de relatórios corrigida: relatórios regulares → /edit, "Aguardando Aprovação" → /review
- Campo "Funcionários" adicionado na seção Informações da Obra (mostra nomes dos funcionários ativos)
- "Descrição" renomeado para "Informações Adicionais"

**December 15, 2025** - Sistema de status de obras atualizado:
- Adicionado status "Não iniciado" às opções disponíveis
- Status agora são: "Não iniciado", "Ativo", "Pausado", "Concluído"
- Botão "Reativar Obra" substituído por dropdown "Alterar Status" (apenas usuários master)
- Dropdown permite alterar para qualquer status diretamente na tela da obra
- Renomeado "Informações do Projeto" para "Informações da Obra" em todas as áreas do sistema
- PDFs de relatório atualizados com nova nomenclatura

**December 15, 2025** - Google Calendar export improvements:
- Added multi-select functionality with checkboxes to select multiple visits at once
- Added "Selecionar Todas" option for bulk selection
- Toggle between "Mostrar Apenas Novas" and "Mostrar Todas" (including already exported)
- Visual indicator (badge) for visits already exported to Google Calendar
- Visits are now marked as exported only after user confirms export
- Re-export functionality: users can export the same visit multiple times if needed

**December 15, 2025** - Temporary approver multi-project selection and permission improvements:
- Updated temporary approver form to allow selecting multiple projects at once (Ctrl/Cmd + click)
- Approver selection is now first, then project selection for better UX
- Review button visibility now properly checks `current_user_is_aprovador(project_id)` for each report
- Global approvers see all pending reports; temporary approvers only see reports from their assigned projects
- Added permission check to `approve_report` and `review_report` routes to prevent direct URL access
- Both global and temporary approvers can approve reports following the standard approval flow

**November 29, 2025** - Checklist UI improvements:
- Observation textareas now only display for checked checklist items (hidden by default, shown on check)
- Approved report view (detail.html) correctly filters to show only selected checklist items
- Comprehensive boolean normalization to handle various truthy value formats across templates
- Improved ID stability for checklist items to maintain observation persistence

**November 21, 2025** - Enhanced project listing with tabs and distance-based sorting:
- Implemented tabbed interface for project filtering: "Obras Ativas" (default) and "Obras Concluídas"
- Client-side geolocation-based distance sorting using Haversine formula
- Visual distance badges on project cards (automatically shows km or m)
- Loading spinner and success alert during distance calculation
- Search and filter forms preserve tab selection with hidden status field
- Graceful degradation: falls back to original order if geolocation unavailable or denied
- Projects without coordinates appear at end of sorted list
- 5-minute geolocation cache for improved performance

**November 19, 2025** - Comprehensive permission system overhaul:
- Created centralized `can_edit_report()` helper function with clear access control rules:
  - Master users can edit ANY report (including Approved/Finalized)
  - Non-master users can edit ONLY their own reports in editable statuses
  - Robust ID comparison with type conversion to prevent permission bypasses
  - Security: Removed permissive fallback for reports without author
- Applied helper function to 15+ critical routes: report_edit, view_report, autosave, photo upload/delete, status updates, submission for approval, and more
- Fixed `report_submit_for_approval` to allow submissions from multiple editable statuses: ['preenchimento', 'Rascunho', 'Rejeitado', 'Em edição', 'Aguardando Aprovação']
- Added detailed logging for permission debugging
- Confirmed end-to-end: non-master users can create reports, edit their own reports, and submit for approval; master users retain full override rights

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
- **File Handling**: Manages file uploads (photos, documents) with a 50MB limit per file, supporting binary image storage in the database with filesystem fallback, and enforced validation with HTTP 413 response for oversized uploads.
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
- **Core Entities**: Users, Projects, Visits, Reports, Reimbursements, Checklist Templates, Communications, Notifications, Global and Temporary Approvers.
- **Projects**: Includes `numeracao_inicial` for custom sequential report numbering.
- **Reports**: Includes `acompanhantes` (JSONB), `lembrete_proxima_visita` (TIMESTAMP), `categoria`, `local`, `observacoes_finais` (TEXT), `criado_por`, and `atualizado_por`.
- **Photo Storage**: Stores binary image data, JSONB for annotation metadata, SHA-256 hash for deduplication, MIME type, and file size. Each photo card displays optional **Categoria**, optional **Local**, and mandatory **Legenda**. `FotoRelatorio` includes `url`, `legenda` (TEXT), `ordem` (INTEGER) for drag-drop reordering, and cascade delete on parent report removal.
- **Notifications**: Tracks report status changes, origin/destination users, message content, type, read status, and email delivery.
- **Aprovador Global**: Single system-wide approver with exclusive permissions to transfer role and manage temporary approvers.
- **Aprovadores Temporários**: Project-specific approvers, managed by the Aprovador Global.
- **Checklist Individual por Obra**: Customizable checklists per project based on a global template.

## Key Features
- **Project Management**: CRUD operations, automatic numbering, GPS location, dynamic categories, project reactivation, and project-specific checklists. **Tabbed listing interface**: separate views for active (Ativo/Pausado) and completed (Concluído) projects with status preservation across searches. **Distance-based sorting**: automatic client-side geolocation sorting with visual distance badges and graceful fallback.
- **Visit Tracking**: GPS-enabled logging, custom checklists, team communication.
- **Report System**: Professional PDF reports with photo annotation, ELP branding, and an approval workflow with email notifications. Reports are numbered sequentially per project. Reminders for next visits are displayed. **AutoSave System**: Fully functional and silent with 2s debounce, automatic persistence of all fields including text, dates, coordinates, checklists, `acompanhantes`, and image files with temporary upload; retry logic, localStorage fallback, automatic report creation on first save, and complete console logging for diagnostics.
- **Photo Management**: Advanced editing (drawing, arrows, text, captions), up to 50 photos per report, predefined caption management, deduplication. Drag-and-drop reordering, real-time synchronization, 50MB file size limit per image. Images are automatically uploaded via `/api/uploads/temp` during autosave, then promoted to permanent storage with full metadata (categoria, local, legenda).
- **REST API**: Complete RESTful API for reports with POST/GET/PUT/DELETE endpoints, atomic transactions with rollback, and comprehensive validation. **AutoSave endpoint**: `/api/relatorios/autosave` accepts partial updates and creates drafts automatically, processes temporary image uploads (temp_id), and returns image IDs for client-side mapping.
- **Client Email Management**: CRUD system for client emails per project with report reception options.
- **Internal Notifications System**: Database-stored notifications with automatic email alerts and push notifications for report status changes.
- **User Management**: Role-based access control.
- **Approval Management System**: Global and temporary approvers with strict permission enforcement and CSRF protection.
- **Calendar System**: Visit scheduling, Google Calendar export.
- **Offline Functionality & PWA**: Full offline support, local storage, automatic sync.
- **Push Notifications**: Proximity alerts, system updates, pending report notifications.

## Security Implementation
- **CSRF Protection**: All forms include CSRF protection.
- **Authentication**: Session-based login with password hashing.
- **File Security**: Secure filename handling and file type validation.
- **Access Control**: Route protection based on login status and user roles.
- **Aprovador Global Permission System**: Strict permission controls for global and temporary approver management, enforced at the backend and reflected in the UI.

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

## Email Integration
- **SMTP**: Configurable mail server.

## PDF and Media Processing
- **WeasyPrint**: Primary PDF generation.
- **Pillow**: Image processing.
- **Canvas API**: JavaScript for photo annotation.

## Cloud Services
- **Firebase Cloud Messaging (FCM)**: Push notifications.
- **Google Drive API**: Automatic backups.
- **ipapi.co**: Geolocation fallback.
- **geopy**: Geocoding and precise distance calculations.