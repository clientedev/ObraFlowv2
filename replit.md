# Overview

This is a comprehensive construction site visit tracking system built with Flask. The system provides advanced project management capabilities including user authentication, project creation, visit scheduling and communication, professional report generation with photo annotation tools, approval workflows, and expense tracking. Enhanced with PDF generation, photo editing capabilities, and admin approval processes for complete construction project oversight.

## Recent Changes (2025-08-18)
- Successfully migrated from Replit Agent to standard Replit environment
- Enhanced project creation form with text input for project type instead of dropdown selection
- Added GPS location capture functionality for project addresses
- Implemented interactive map selection for project locations using Leaflet.js
- Updated database schema to support GPS coordinates (latitude/longitude) for projects
- Configured PostgreSQL database for production use
- Fixed database schema issues by adding missing columns (latitude, longitude, tipo_obra)
- Application fully functional with admin user (admin/admin123)
- Project form now allows free text input for construction type and location selection via GPS or interactive map

### Latest Updates (Evening 2025-08-18)
- ✅ **Photo Editor Fixed**: Complete photo annotation system with drawing tools (pen, arrow, rectangle, circle, text)
- ✅ **Report System Functional**: Reports saving correctly with photos, fixed UI feedback issues
- ✅ **PDF Generation**: Professional PDF reports matching template format with photos and signatures
- ✅ **GPS Homepage**: Interactive map showing nearest construction sites based on user location
- ✅ **Database Configuration**: Upload folder configured, file handling improved
- ✅ **Complete Workflow**: Full report creation, editing, photo annotation, and PDF generation working

### Critical Fixes (2025-08-19 Morning)
- ✅ **50 Photo Limit**: Successfully increased from 5 to 50 photos per report in form_complete.html
- ✅ **GPS Address Formatting**: GPS now returns formatted addresses instead of raw coordinates
- ✅ **Dashboard Proximity**: Works showing projects ordered by distance with proper API endpoints
- ✅ **CSRF Issues Resolved**: API endpoints exempted from CSRF for proper functionality
- ✅ **Visual Indicators**: Added clear UI markers showing "50 fotos" and "NOVO" features
- ✅ **Dashboard Simplification**: Removed map interface, created simple list view of nearby projects
- ✅ **Enhanced PDF Checklist**: Improved checklist formatting with colored tables, icons, and professional layout

### Latest Updates (2025-08-19 Evening)
- ✅ **ELP Brand Identity**: Complete implementation of ELP Consultoria e Engenharia visual identity
- ✅ **Logo Integration**: Added ELP logo to navbar and all PDF reports with company information
- ✅ **Brand Colors**: Updated color scheme to match ELP brand (dark gray #343a40 and cyan #20c1e8)
- ✅ **PDF Branding**: Enhanced PDFs with ELP header, signatures, and footer branding
- ✅ **Company Information**: Updated all references to reflect ELP's specialization in civil engineering and facades

### Final Updates (2025-08-19 Night)
- ✅ **New Logo Implemented**: Updated to new ELP logo (elp_1755609978629.jpg) with transparent background
- ✅ **Dashboard Enhanced**: Added "Relatórios Recentes" section showing last 5 reports with status and quick access
- ✅ **Contact Functions Removed**: Eliminated all contact-related buttons and functionality per user request
- ✅ **Nearby Projects Fixed**: GPS-based project discovery fully functional with distance ranking (🥇🥈🥉)
- ✅ **PDF Improvements**: Enhanced checklist formatting with colored icons (✅❌), professional photo grids
- ✅ **API Corrections**: Fixed nearby projects API to work without authentication requirements
- ✅ **Reimbursement Routes**: Corrected template references to prevent application errors

### Calendar System Implementation (2025-08-19 Evening)
- ✅ **Database Models**: Created ChecklistTemplate, ChecklistItem, and ComunicacaoVisita models
- ✅ **PostgreSQL Tables**: Added missing database tables with proper relationships
- ✅ **Calendar System Fixed**: Resolved all import errors and relationship issues
- ✅ **Form Processing**: Enhanced visit creation with datetime-local input handling
- ✅ **Default Templates**: Created default checklist templates (Inspeção Visual, Fixações, Segurança, Documentação)
- ✅ **Export Functions**: Fixed Google Calendar export with proper timedelta imports
- ✅ **Error Resolution**: Eliminated 500 errors in visit listing and checklist functions
- ✅ **Complete Workflow**: Visit scheduling, calendar view, and export fully operational

### Complete System Overhaul (2025-08-19 Final)
- ✅ **Complete PDF Generation**: Rebuilt PDF system to include ALL report data with professional ELP branding
- ✅ **Report Deletion Fixed**: Enhanced deletion with proper photo file cleanup and error handling
- ✅ **Image Visualization Enhanced**: Added modal popups for photo viewing with click-to-expand functionality
- ✅ **Professional PDF Format**: New comprehensive layout with ELP header, complete data sections, GPS info, author details, and formatted checklists
- ✅ **Data Integrity**: PDF now includes all report fields: number, title, dates, status, project info, GPS coordinates, author, approval info, complete content, and professional photos
- ✅ **ELP Branding Complete**: Professional header with logo, company information, contact details, and branded color scheme throughout PDF
- ✅ **Clean PDF Format**: Final PDF shows only filled data and checked checklist items without status labels (conforme/não conforme)

### Photo System Enhancement (2025-08-20)
- ✅ **Photo Upload System Fixed**: Resolved "allowed_file not defined" error preventing report saves
- ✅ **FormData Implementation**: JavaScript now properly sends photo files with FormData instead of just metadata
- ✅ **AJAX Response Handling**: Server returns JSON responses for proper AJAX form submission feedback
- ✅ **Smart Photo Processing**: When photos are edited, only the edited version is saved and original is discarded
- ✅ **Visual Editing Feedback**: UI shows when photos have been edited with status indicators
- ✅ **50 Photo Support**: System supports up to 50 photos per report with proper file handling

### System Fixes (2025-08-20 Final)
- ✅ **Map Address Capture**: Project creation map now properly fills address field when location is selected
- ✅ **Outlook Calendar Export**: Fixed ICS file format with proper line breaks and headers for Outlook compatibility
- ✅ **Reimbursement Form**: Updated to use separate date picker fields for start and end dates
- ✅ **CSRF Token Issues**: Resolved reimbursement form submission errors by adding proper CSRF exemption
- ✅ **Template Routing**: Fixed URL routing errors in reimbursement list template
- ✅ **Data Field Mapping**: Corrected reimbursement display fields to match database schema

### Offline Functionality Implementation (2025-08-20)
- ✅ **Service Worker**: Complete offline support with caching strategies for pages and assets
- ✅ **Offline Manager**: JavaScript system for detecting connection status and managing offline data
- ✅ **Local Storage**: Form data automatically saved locally when offline
- ✅ **Auto Sync**: Automatic synchronization when connection is restored
- ✅ **Status Indicators**: Visual feedback showing offline/online status and pending sync items
- ✅ **Background Sync**: Service Worker handles background synchronization
- ✅ **Offline Forms**: All major forms (reports, visits, projects, reimbursements) work offline
- ✅ **Data Management**: Local data viewer and management interface for offline data

### PWA (Progressive Web App) Implementation (2025-08-20)
- ✅ **PWA Manifest**: Complete manifest.json with app metadata, icons, and shortcuts
- ✅ **App Icons**: Multiple icon sizes (72x72 to 512x512) generated from ELP logo
- ✅ **Installation Support**: Automatic detection and installation prompts for Android/iOS/Desktop
- ✅ **Native App Experience**: Standalone display mode with native app appearance
- ✅ **Cross-Platform**: Works on Android (Chrome/Firefox), iOS (Safari), and Desktop browsers
- ✅ **Installation Guide**: Complete guide page with step-by-step instructions for all platforms
- ✅ **Offline Capabilities**: Full PWA offline functionality with Service Worker
- ✅ **Home Screen Shortcuts**: Quick access to create reports, visits, and view projects

### Push Notifications System (2025-08-20)
- ✅ **Proximity Alerts**: Notificações quando usuário se aproxima de obras (raio de 500m)
- ✅ **System Updates**: Alertas sobre novidades no app e relatórios pendentes para administradores
- ✅ **Geolocation Monitoring**: Monitoramento contínuo de localização para detecção de proximidade
- ✅ **Background Sync**: Service Worker com suporte a notificações push e sincronização em background
- ✅ **Dashboard Integration**: Painel de controle de notificações integrado ao dashboard principal (discreto)
- ✅ **Permission Management**: Sistema completo de gerenciamento de permissões de notificação
- ✅ **Cross-Platform Support**: Funciona em Android, iOS (PWA) e Desktop com adaptações específicas
- ✅ **iOS Compatibility**: Suporte específico para Safari iOS com instruções detalhadas de instalação

### Error Handling & System Stability (2025-08-20)
- ✅ **404/500 Error Templates**: Páginas de erro profissionais com navegação de retorno
- ✅ **Missing Templates**: Criados templates faltantes (reimbursements/form.html, error pages)
- ✅ **Route Fixes**: Corrigidos conflitos de rotas e referências incorretas em templates
- ✅ **Notification UI**: Interface de notificações tornada mais discreta conforme solicitado
- ✅ **Form Validation**: Correção de referências de rotas em formulários (report_create → create_report)
- ✅ **PWA Assets**: Verificação de disponibilidade de manifest.json e service worker

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM for database operations
- **Database**: SQLite for development with PostgreSQL support configured via environment variables
- **Authentication**: Flask-Login for session management with role-based access (regular users vs master users)
- **Forms**: WTForms with CSRF protection for secure form handling
- **File Handling**: File upload system for photos and documents with size limits (16MB max)

## Frontend Architecture
- **Templates**: Jinja2 templating engine with Bootstrap 5 for responsive UI
- **Styling**: Custom CSS with construction industry color themes (orange, yellow, blue)
- **JavaScript**: Vanilla JavaScript for form validation, photo preview, and location services
- **Components**: Modular template structure with base template and specialized forms

## Data Model Design
- **Users**: Authentication with roles (master/regular), contact information, and project assignments
- **Projects**: Sequential numbering system, status tracking, and type categorization
- **Visits**: Scheduling system with GPS coordinates, checklist templates, and status workflow
- **Reports**: Document generation with photo attachments and email distribution
- **Reimbursements**: Expense tracking with categorized costs and approval workflow

## Key Features
- **Project Management**: CRUD operations with automatic numbering (PROJ-0001 format)
- **Visit Tracking**: GPS-enabled visit logging with customizable checklists and team communication
- **Enhanced Report System**: Professional PDF generation with photo annotation tools and approval workflows
- **Photo Management**: Advanced photo editing with drawing tools, arrows, text annotations, and captions
- **Communication System**: Visit-based messaging for team collaboration and progress tracking
- **Approval Workflow**: Admin approval process for reports before distribution
- **User Management**: Role-based access with master user privileges and approval authority
- **File Management**: Secure file uploads with proper validation and storage

## Security Implementation
- **CSRF Protection**: All forms protected against cross-site request forgery
- **Authentication**: Session-based login with password hashing
- **File Security**: Secure filename handling and file type validation
- **Access Control**: Route protection with login requirements and role checks

# External Dependencies

## Core Flask Ecosystem
- **Flask-SQLAlchemy**: Database ORM for model definitions and queries
- **Flask-Login**: User session management and authentication
- **Flask-Mail**: Email functionality for report distribution
- **Flask-WTF**: Form handling with CSRF protection and file uploads
- **WTForms**: Form validation and rendering

## Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive design and components
- **Font Awesome 6**: Icon library for consistent UI elements
- **JavaScript APIs**: Geolocation API for GPS coordinates, File API for photo handling

## Database Support
- **SQLite**: Default development database
- **PostgreSQL**: Production database support via DATABASE_URL environment variable

## Email Integration
- **SMTP**: Configurable mail server (defaults to Gmail SMTP)
- **Environment Variables**: MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD for email configuration

## Development Tools
- **Werkzeug**: WSGI utilities including ProxyFix for deployment
- **Python Logging**: Debug logging configuration for development

## PDF and Media Processing
- **ReportLab**: Professional PDF generation with custom styling and layouts
- **Pillow**: Image processing for photo annotations and resizing
- **Canvas API**: JavaScript-based photo annotation tools with drawing capabilities