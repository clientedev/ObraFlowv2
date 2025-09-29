# Overview
This project is a comprehensive construction site visit tracking system built with Flask, designed to streamline site management, improve communication, and ensure efficient documentation and oversight in the construction industry. It offers advanced project management, user authentication, visit scheduling, professional report generation with photo annotation, approval workflows, and expense tracking. The system aims to provide complete oversight for construction projects, with market potential in civil engineering and facade specialization.

# Recent Changes (September 29, 2025)

## Customizable Category Lists per Project (Item 16)
**Feature:** Each project can now have its own custom categories for organizing photos in reports, replacing the previous hardcoded category system.

**Implementation:**
1. **Database Schema:**
   - Created `categorias_obra` table with fields: `id`, `projeto_id`, `nome_categoria`, `ordem`, `created_at`, `updated_at`
   - Migration: `20250929_2303_add_categorias_obra_table.py`
   - Foreign key relationship to `projetos` table

2. **Backend (models.py & routes.py):**
   - Added `CategoriaObra` model with relationship to `Projeto`
   - Created CRUD API endpoints:
     - `GET /projects/<id>/categorias` - List all categories for a project
     - `POST /projects/<id>/categorias/add` - Create new category
     - `PUT /projects/<id>/categorias/<cat_id>/edit` - Update category
     - `DELETE /projects/<id>/categorias/<cat_id>/delete` - Delete category
   - Updated express report forms to load dynamic categories based on `projeto_id` parameter

3. **Frontend UI (templates/projects/view.html):**
   - Added "Categorias" tab to project view page
   - JavaScript functions for category management:
     - `carregarCategorias()` - Loads categories via API
     - `adicionarCategoria()` - Creates new category
     - `editarCategoria()` - Updates category name
     - `excluirCategoria()` - Deletes category with confirmation
   - Bootstrap-styled list interface with edit/delete buttons

4. **Dynamic Form Integration:**
   - Express report forms (`express_new` route) now check for `projeto_id` query parameter
   - If project has custom categories, they replace default hardcoded options
   - Fallback to default categories (Torre 1, Torre 2, Área Comum, Piscina) if none exist

**Benefits:**
- Projects can define specific categories relevant to their construction type
- Examples: Multi-tower buildings can have "Torre 1", "Torre 2"; Simple projects can use "Fachada", "Interior"
- More flexible photo organization in reports
- Each project's categories are independent

## Replit Environment Setup
- ✅ Installed Python 3.11 with all dependencies
- ✅ Configured PostgreSQL database connection
- ✅ Set up Flask workflow on port 5000 with 0.0.0.0 host
- ✅ Configured deployment with gunicorn for production (autoscale)

## Report Numbering Fix - Per-Project Sequential Numbering
**Issue:** Reports were using global numbering, causing conflicts between different projects.

**Solution Implemented:**
1. **Database Schema Update:**
   - Added `numero_projeto` column for per-project sequential numbering
   - Changed `numero` column from globally unique to unique per project
   - Added composite unique constraint `uq_relatorios_projeto_numero` on `(projeto_id, numero)`

2. **Report Creation Logic (routes.py):**
   - Gets max `numero_projeto` for the specific project
   - Increments to get next sequential number
   - Formats as `REL-XXXX` (e.g., REL-0001, REL-0002)

3. **How It Works:**
   - Each project has independent numbering starting from REL-0001
   - Project A: REL-0001, REL-0002, REL-0003...
   - Project B: REL-0001, REL-0002, REL-0003...
   - Sequential numbering maintained within each project

4. **Migration Files:**
   - `20250928_1300_add_numero_projeto_to_relatorios.py` - Added numero_projeto column
   - `20250929_2100_fix_numero_unique_constraint_per_project.py` - Fixed unique constraints

## Report Form Redirect Fix (September 29, 2025)
**Issue:** After creating a report, the browser displayed raw JSON instead of redirecting to the reports list.

**Root Cause:** The form submission had two conflicting event listeners:
1. First listener (lines 1486-1592): Uses `fetch()` to submit form and expects JSON response
2. Second listener (lines 2710-2746): Validates and processes photos, then called `form.submit()`

The `form.submit()` method bypasses all event listeners, submitting the form normally. The server returned JSON (for the fetch handler), but since fetch wasn't used, the browser displayed the raw JSON.

**Solution:**
- Changed line 2736 from `form.submit()` to `form.dispatchEvent(submitEvent)`
- This triggers the fetch-based submit handler properly
- The fetch handler receives JSON, processes it, and redirects via `window.location.href`

**Result:** Form now correctly redirects to `/reports` after successful submission.

## Login Credentials
- **Username:** admin
- **Password:** admin123

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

## Frontend Architecture
- **Templates**: Jinja2 templating engine, styled with Bootstrap 5.
- **Styling**: Custom CSS aligned with construction industry themes and ELP brand identity (dark gray, cyan).
- **JavaScript**: Vanilla JS for form validation, photo previews, and location services via Leaflet.js.
- **UI/UX**: Mobile-first design, PWA for installability and offline functionality, touch event optimization for photo editor on mobile.

## Data Model Design
- **Users**: Authentication, roles, contact info, project assignments.
- **Projects**: Sequential numbering, status tracking, categories, GPS coordinates.
- **Visits**: Scheduling, GPS logging, customizable checklist templates, status workflows.
- **Reports**: Document generation with photos, email distribution.
- **Reimbursements**: Expense tracking with categories and approval workflow.
- **Checklist Templates**: Defines `ChecklistTemplate` and `ChecklistItem`.
- **ComunicacaoVisita**: Model for visit-based communication.

## Key Features
- **Project Management**: CRUD operations for projects, automatic numbering, GPS location.
- **Visit Tracking**: GPS-enabled logging, custom checklists, team communication.
- **Enhanced Report System**: Professional PDF reports with photo annotation, ELP branding, and approval workflow.
- **Professional PDF Generation**: Dual system with WeasyPrint (primary for pixel-perfect HTML/CSS templates) and ReportLab (legacy) for Artesano template format.
- **Client Email Management**: CRUD system for client emails per project with duplicate prevention.
- **Photo Management**: Advanced photo editing (drawing, arrows, text, captions), support for up to 50 photos per report, and predefined caption management.
- **Communication System**: Visit-based messaging for collaboration.
- **Approval Workflow**: Admin approval for reports.
- **User Management**: Role-based access control.
- **Calendar System**: Visit scheduling, Google Calendar export, default checklist templates.
- **Offline Functionality & PWA**: Full offline support, local storage for form data, automatic sync, and PWA manifest.
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