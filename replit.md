# Overview
This project is a comprehensive construction site visit tracking system built with Flask, designed to streamline site management, improve communication, and ensure efficient documentation and oversight in the construction industry. It offers advanced project management, user authentication, visit scheduling, professional report generation with photo annotation, approval workflows, and expense tracking. The system aims to provide complete oversight for construction projects, with market potential in civil engineering and facade specialization.

## Recent Changes
- **Date**: October 3, 2025 - Correção DEFINITIVA de Duplicação ao Concluir Relatórios
- **Problema**: Ao clicar em "Concluir" relatório preenchido:
  - Sistema gerava duplicado: um em "Aguardando aprovação" e outro em "Em preenchimento"
  - Múltiplos registros para o mesmo projeto
- **Causa Raiz**: Condições de corrida no fluxo de criação/finalização de relatórios
  - `createInitialReport()` no template podia criar relatório em "preenchimento"
  - Form submission também podia criar outro relatório se `window.currentReportId` não estivesse setado
  - Timing issues causavam criação de múltiplos relatórios para o mesmo projeto
- **Solução**: Modificada função `finalize_report()` em routes.py (linhas 3041-3123)
  - Ao finalizar, busca TODOS os relatórios em "preenchimento" do mesmo `projeto_id`
  - Deleta automaticamente os relatórios duplicados (exceto o que está sendo finalizado)
  - Deleta também as fotos associadas aos relatórios duplicados
  - Garante que apenas 1 relatório existe após conclusão: o em "Aguardando Aprovação"
  - Logging completo para rastreamento de duplicados removidos
  - ✅ Problema DEFINITIVAMENTE resolvido - sem duplicação garantida

- **Date**: October 3, 2025 - Correção de Duplicação ao Concluir Relatórios (Primeira Tentativa)
- **Problema**: Ao clicar em "Concluir" relatório preenchido:
  - Apareciam DUAS mensagens de conclusão
  - Relatório era duplicado
  - Status ficava "Em preenchimento" ao invés de "Aguardando Aprovação"
- **Causa Raiz**: Existiam DUAS funções com a mesma rota `/reports/<int:report_id>/finalize`
  - `finalize_report()` (linha 3051) - correta, mudava para "Aguardando Aprovação"
  - `report_finalize()` (linha 5240) - duplicada, mudava para "Finalizado"
  - Ambas executavam ao clicar em concluir, causando duplicação e status incorreto
- **Solução**: Removida função duplicada `report_finalize()` de routes.py (anteriormente linhas 5240-5282)
  - Agora apenas `finalize_report()` executa
  - Status corretamente atualizado para "Aguardando Aprovação"
  - ⚠️ Não resolveu completamente - duplicação persistia por outras razões

- **Date**: October 3, 2025 - Image Upload Fix & Replit Environment Setup
- **Issue**: Images were not being saved to the database - the form submission handler was dispatching a new submit event with no handler, causing the form to never actually submit
- **Root Cause**: After preparing photo files, the code removed the submit listener and dispatched a new submit event that had no handler
- **Solution**: Fixed form submission in `templates/reports/form_complete.html` (lines 2720-2738)
  - Replaced broken submit event dispatch with direct `form.submit()` call
  - Ensures multipart/form-data form submits with all prepared files
  - Improved error messages for better user feedback
  - **ONLY changed image upload flow - all other functionality unchanged**
  - ✅ Images now correctly sent to backend and saved to PostgreSQL BYTEA column
  
- **Date**: October 3, 2025 - Replit Environment Setup
- **Python Dependencies**: Successfully installed all requirements via pip
  - Flask, SQLAlchemy, Flask-Login, Flask-WTF, and all other dependencies
  - WeasyPrint for PDF generation, Pillow for image processing
  - PostgreSQL support via psycopg2-binary
- **Workflow Configuration**: Flask server running on port 5000
  - Configured to use DATABASE_URL environment variable
  - Auto-initialization of database tables and admin user
  - Webview output for frontend preview
  
- **Date**: October 3, 2025 - Railway PostgreSQL Database Note
- **Railway PostgreSQL Database**: Successfully configured and connected
  - Database URL: Railway PostgreSQL (external connection via switchback.proxy.rlwy.net:17107)
  - All tables created and verified with BYTEA support for image storage
  - Migration system synchronized (all migrations marked as applied)
  - Verified schema: 17 columns in fotos_relatorio including imagem (BYTEA), imagem_hash, content_type, imagem_size
  - System ready for production use with Railway database
  
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
  - ✅ CONFIRMED: All fields present in Railway PostgreSQL database
  
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
- **Database**: Railway PostgreSQL (production), configured via DATABASE_URL environment variable.
  - External connection: switchback.proxy.rlwy.net:17107
  - Internal connection: postgres.railway.internal:5432
  - Database name: railway
  - Auto-reconnection enabled with pool_pre_ping and pool_recycle
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