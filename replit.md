# Overview
This project is a comprehensive construction site visit tracking system built with Flask, designed to streamline site management, improve communication, and ensure efficient documentation and oversight in the construction industry. It offers advanced project management, user authentication, visit scheduling, professional report generation with photo annotation, approval workflows, and expense tracking. The system aims to provide complete oversight for construction projects, with market potential in civil engineering and facade specialization.

# User Preferences
Preferred communication style: Simple, everyday language.
Mobile-first design: Date field should be the first input field in report forms.

# Replit Environment Setup
- **Python Version**: Python 3.11 with full toolchain (pip, poetry, pyright, debugpy)
- **Database**: PostgreSQL (via Replit database service)
- **Development Server**: Flask development server on port 5000 (host: 0.0.0.0)
- **Production Server**: Gunicorn with 4 workers (configured for VM deployment)
- **System Dependencies**: pango, cairo, gdk-pixbuf, harfbuzz, libffi (for WeasyPrint PDF generation)
- **Entry Point**: main.py
- **Default Admin**: username: admin, password: admin123 (created on first run)

# Recent Improvements (October 2025)

## Chrome Mobile & PWA Permission Fix - User Gesture Context (October 1, 2025 - Latest)
- **Critical Fix for Mobile**: Rewrote `toggleNotifications()` to call `getCurrentPosition()` **synchronously** within click event
  - ✅ **No await/setTimeout before getCurrentPosition()** - maintains user gesture context required by Chrome Mobile
  - ✅ **Direct call in click handler** - browser recognizes it as user-initiated action
  - ✅ **maximumAge: 0** - forces fresh permission prompt (no cached position)
  - ✅ **enableHighAccuracy: true** - requests best accuracy available
  - ✅ Works on: Desktop Chrome, Chrome Mobile, PWA (standalone), and APK/WebView
- **Sequential Permission Flow**: 
  1. User clicks "Ativar" button
  2. `getCurrentPosition()` called **immediately** (synchronous)
  3. Location permission prompt appears FIRST
  4. After location granted → `Notification.requestPermission()` called
  5. Notification permission prompt appears SECOND
  6. Both granted → System activates with user position
- **Error Handling**:
  - Location denied (code 1) → Shows clear message to enable in browser settings
  - Other errors → Shows specific error message
  - Notification denied → Shows warning that proximity alerts won't work

## Mandatory Location Validation for Notifications (October 1, 2025)
- **Backend Location Validation**: Updated `/api/notifications/subscribe` endpoint to require and validate location coordinates
  - ✅ Validates both notification subscription AND location coordinates are provided
  - ✅ Validates latitude range (-90 to 90) and longitude range (-180 to 180)
  - ✅ Returns error if location data is missing or invalid
  - ✅ Logs successful activations with user location for proximity alerts
- **Frontend Location Capture**: Enhanced `subscribeToPush()` in `notifications.js`
  - ✅ Captures current location with high accuracy before sending subscription
  - ✅ Includes latitude, longitude, and accuracy in subscription request
  - ✅ Shows clear error message if location permission is denied
  - ✅ Prevents notification activation if location is not available
- **Dual Permission Flow**: Ensures both permissions are required together
  - ✅ User must grant BOTH notification AND location permissions
  - ✅ Clear error messages explain why each permission is needed
  - ✅ System only activates when both permissions are granted successfully

## Dual Permission System for Location & Notifications (October 1, 2025)
- **Enhanced Permission Flow**: Sistema agora solicita AMBAS permissões (localização E notificação) sequencialmente
  - **SEMPRE pede localização PRIMEIRO** (independente do status de notificação)
  - Depois solicita permissão de notificações push
  - Só ativa o sistema completo se ambas forem concedidas
  - Mensagens claras ao usuário explicando cada permissão
- **Nearby Projects API**: Endpoint `/api/projects/nearby` (POST) com:
  - Cálculo de distância usando fórmula Haversine
  - Filtro por raio configurável (padrão 10km)
  - **CSRF exempt** (@csrf.exempt) para aceitar requisições JSON
  - Requer autenticação (@login_required)
  - Retorna obras ordenadas por proximidade
- **Frontend Integration**: Função `localizarObrasProximas()` em `main.js`
  - Obtém localização do usuário com alta precisão (maximumAge: 0)
  - Envia coordenadas para API via POST JSON
  - Renderiza resultados em lista visual com distâncias
  - Tratamento robusto de erros de geolocalização
- **Security**: Meta tag `csrf-token` em `base.html` para requisições AJAX seguras

## Geolocation and Railway Integration Fixes (October 1, 2025)
- **Flask-CORS Integration**: Added Flask-CORS 5.0.0 to enable proper API calls from frontend
  - Configured CORS with credentials support for `/api/*` and `/save_location` routes
  - Resolves "User denied Geolocation" errors caused by CORS restrictions
- **New /save_location Route**: Created dedicated endpoint for geolocation tracking
  - Validates latitude/longitude ranges (-90 to 90, -180 to 180)
  - Logs user location with source (GPS/IP), accuracy, and address
  - Supports optional project_id and relatorio_id for context binding
  - Returns proper JSON responses with error handling
- **HTTPS Enforcement**: Added automatic HTTPS redirect for Railway production
  - Uses `@app.before_request` hook to enforce HTTPS in RAILWAY_ENVIRONMENT
  - Exempts health check endpoints from redirect
  - Works with existing ProxyFix middleware configuration
- **Requirements Cleanup**: Removed duplicate packages from requirements.txt
  - Consolidated to single entries for each package
  - Added Flask-CORS as new dependency

## Geolocation System Enhancement
- **Enhanced Geolocation Module** (`static/js/geolocation-enhanced.js`): Sistema robusto de geolocalização com:
  - **HTTPS Enforcement**: Detecta e avisa se não estiver em HTTPS
  - **Error Handling**: Tratamento detalhado de erros com mensagens específicas por dispositivo/navegador
  - **IP Fallback**: Fallback automático para geolocalização por IP (ipapi.co) quando GPS falha
  - **Reverse Geocoding**: Conversão automática de coordenadas em endereço legível
  - **Platform-Specific Instructions**: Instruções customizadas para Android, iOS, Chrome, Firefox, Safari
  - **maximumAge = 0**: Sempre força localização fresca (resolve cache issues)
  - **Watch Location**: Monitoramento contínuo com tratamento robusto de erros
- **Integration**: Sistema integrado em `main.js` e `notifications.js` para captura consistente de localização
- **User Experience**: Modais informativos com instruções claras quando permissão é negada ou GPS indisponível

# System Architecture

## Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM.
- **Database**: PostgreSQL for production, SQLite for development.
- **Authentication**: Flask-Login for session management and role-based access (regular/master users).
- **Forms**: WTForms for secure form handling and CSRF protection.
- **File Handling**: Manages file uploads (photos, documents) with a 16MB size limit, supporting binary image storage directly in the database with filesystem fallback.

## Frontend Architecture
- **Templates**: Jinja2 templating engine, styled with Bootstrap 5.
- **Styling**: Custom CSS aligned with construction industry themes and ELP brand identity (dark gray, cyan).
- **JavaScript**: Vanilla JS for form validation, photo previews, and location services via Leaflet.js.
- **UI/UX**: Mobile-first design, PWA for installability and offline functionality, touch event optimization for photo editor on mobile.

## Data Model Design
- **Users**: Authentication, roles, contact info, project assignments.
- **Projects**: Sequential numbering (per-project), status tracking, categories (customizable per-project), GPS coordinates.
- **Visits**: Scheduling, GPS logging, customizable checklist templates, status workflows.
- **Reports**: Document generation with photos, email distribution.
- **Reimbursements**: Expense tracking with categories and approval workflow.
- **Checklist Templates**: Defines `ChecklistTemplate` and `ChecklistItem`.
- **ComunicacaoVisita**: Model for visit-based communication.

## Key Features
- **Project Management**: CRUD operations for projects, automatic numbering (per-project), GPS location.
- **Visit Tracking**: GPS-enabled logging, custom checklists, team communication.
- **Enhanced Report System**: Professional PDF reports with photo annotation, ELP branding, and approval workflow.
- **Professional PDF Generation**: Dual system with WeasyPrint (primary for pixel-perfect HTML/CSS templates) and ReportLab (legacy) for Artesano template format.
- **Client Email Management**: CRUD system for client emails per project with duplicate prevention.
- **Photo Management**: Advanced photo editing (drawing, arrows, text, captions), support for up to 50 photos per report, and predefined caption management.
- **Communication System**: Visit-based messaging for collaboration.
- **Approval Workflow**: Admin approval for reports.
- **User Management**: Role-based access control.
- **Calendar System**: Visit scheduling, Google Calendar export, default checklist templates.
- **Offline Functionality & PWA**: Full offline support, local storage for form data, automatic sync, and PWA manifest with ELP logo.
- **Push Notifications**: Proximity alerts for sites, system updates, pending report notifications using geolocation.
- **Google Drive Integration**: Automatic backup of PDFs and images to Google Drive, with project-specific folder organization and manual backup options.

## Security Implementation
- **CSRF Protection**: All forms include CSRF protection.
- **Authentication**: Session-based login with password hashing.
- **File Security**: Secure filename handling and file type validation.
- **Access Control**: Route protection based on login status and user roles, including developer-specific routes.

# External Dependencies

## Core Flask Ecosystem
- **Flask-SQLAlchemy**: ORM for database interactions.
- **Flask-Login**: User session and authentication management.
- **Flask-Mail**: Email functionality.
- **Flask-WTF**: Form handling, CSRF protection, file uploads.
- **WTForms**: Form validation and rendering.

## Frontend Libraries
- **Bootstrap 5**: Responsive design framework.
- **Font Awesome 6**: Icon library.
- **Leaflet.js**: Interactive map selection.
- **JavaScript APIs**: Geolocation API, File API.

## Database Support
- **SQLite**: Development database.
- **PostgreSQL**: Production database.

## Email Integration
- **SMTP**: Configurable mail server (defaulting to Gmail SMTP).

## PDF and Media Processing
- **WeasyPrint**: Primary PDF generation engine using HTML/CSS templates.
- **ReportLab**: Legacy PDF generation system.
- **Pillow**: Image processing for annotations and resizing.
- **Canvas API**: JavaScript for photo annotation and drawing.
- **Google Drive API**: For automatic backups and file organization.