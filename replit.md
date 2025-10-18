# Overview
This project is a comprehensive Flask-based construction site visit tracking system designed to streamline site management, improve communication, and ensure efficient documentation and oversight in the construction industry. It offers advanced project management, user authentication, visit scheduling, professional report generation with photo annotation, approval workflows, and expense tracking. The system aims to provide complete oversight for construction projects, with market potential in civil engineering and facade specialization.

# Recent Changes (October 2025)
## Correção Completa do Fluxo de Categorias da Obra - Item 16 (18 Outubro 2025)
Correção do fluxo de categorias para garantir que sejam carregadas, exibidas e gerenciadas corretamente na tela de edição de obras.

### Problemas Corrigidos
- **Categorias não apareciam na edição**: Ao clicar em editar obra, as categorias cadastradas não eram carregadas nem exibidas
- **Falta de feedback visual**: Operações de adicionar/editar/excluir categorias não mostravam mensagens de sucesso/erro claras
- **Backend incompleto**: Rota `project_edit` não buscava categorias existentes do banco de dados

### Implementações
#### Backend (routes.py)
- **Busca de Categorias** (linha 4464): `CategoriaObra.query.filter_by(projeto_id=project_id).order_by(CategoriaObra.ordem).all()`
- **Passagem para Template** (linha 4540): `categorias=categorias_existentes` adicionado ao render_template
- **Processamento no POST** (linhas 4495-4525): Extrai e salva novas categorias do formulário com verificação de duplicação

#### Frontend (templates/projects/form.html)
- **Carregamento Automático** (linhas 571-602): JavaScript DOMContentLoaded carrega categorias existentes quando em modo edição
- **Exibição Read-Only**: Categorias existentes mostradas com badge "Cadastrada" e orientação para editar/excluir na aba Visualização
- **Preservação do Counter**: `categoriaCounter` incrementado para evitar conflitos com novas categorias

#### Frontend (templates/projects/view.html)
- **Toasts Modernos**: Função `mostrarMensagem()` com Bootstrap alerts posicionados, ícones FontAwesome e auto-dismiss
- **Feedback Contextual**: Mensagens específicas para cada operação (adicionar/editar/excluir) com nome da categoria

### Fluxo Completo Validado
✅ Criar categoria na tela de criação → salvamento no banco
✅ Criar categoria na tela de edição → salvamento no banco
✅ Criar categoria na aba Visualização → salvamento + toast de sucesso
✅ Editar categoria na aba Visualização → atualização + toast de sucesso
✅ Excluir categoria na aba Visualização → deleção + toast de sucesso
✅ Categorias aparecem na criação de relatórios express
✅ Persistência correta no banco Railway PostgreSQL

## Correção de Aprovação e Exclusão de Relatórios - Item 23 (Outubro 2025)
Correção completa das funcionalidades de aprovação e exclusão de relatórios para resolver erros 500 (InFailedSqlTransaction) e implementar envio automático de e-mails com PDF.

### Problemas Corrigidos
- **Erro InFailedSqlTransaction**: Causado por múltiplos commits intercalados com operações de envio de e-mail
- **E-mails limitados**: Sistema anterior enviava apenas para o autor do relatório
- **Exclusão incompleta**: Não deletava registros relacionados (notificações, logs)

### Implementações - Endpoint de Aprovação (`/reports/<int:id>/approve`)
- **Commit Único**: Todas as operações de banco (status + notificação) commitadas ANTES do envio de e-mails (linha 3067)
- **E-mail para Todos os Envolvidos**: 
  - Autor do relatório
  - Responsável do projeto
  - Funcionários da obra (com e-mail cadastrado)
  - Clientes da obra (EmailCliente com receber_relatorios=True)
- **PDF Anexo**: E-mail enviado com PDF do relatório usando `enviar_relatorio_por_email()`
- **Tratamento de Erro Robusto**: Rollback automático, logs detalhados, mensagens amigáveis ao usuário

### Implementações - Endpoint de Exclusão (`/reports/<int:id>/delete`)
- **Exclusão Completa**: Remove fotos físicas, registros de FotoRelatorio, Notificacao, LogEnvioEmail
- **Commit Único**: Todas as exclusões commitadas em uma única transação (linha 3482)
- **Redirect 303**: Retorna redirect com status 303 (See Other) conforme especificação
- **Logs Informativos**: Registra detalhes da exclusão incluindo número de fotos deletadas

### Fluxo de E-mail de Aprovação
**Assunto**: Relatório {numero} aprovado
**Corpo**: O relatório {numero} referente à obra "{obra}" foi aprovado e está disponível no sistema.
**Anexo**: PDF do relatório aprovado
**Remetente**: {aprovador.nome_completo}

## Sistema de Notificações e E-mail (Item 23 - Versão Anterior)
Sistema de notificações internas com envio automático de e-mails:

### Modelo de Dados
- **Tabela `notificacoes`**: Armazena notificações internas com tracking de envio de e-mail

### Funções de E-mail
- `enviar_notificacao_enviado_para_aprovacao()`: Envia e-mail ao aprovador
- `enviar_notificacao_aprovacao()`: Envia e-mail ao autor após aprovação
- Corpo HTML formatado, links diretos, fallback para configurações do sistema

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
- **Core Entities**: Users, Projects (with dynamic categories), Visits, Reports, Reimbursements, Checklist Templates, Communication Records, Notifications.
- **Photo Storage (`FotoRelatorio`)**: BYTEA for binary image data, JSONB for annotation metadata (`anotacoes_dados`, `coordenadas_anotacao`), SHA-256 hash for deduplication (`imagem_hash`), MIME type storage (`content_type`), and file size tracking (`imagem_size`).
- **Notifications (`Notificacao`)**: Internal notification system tracking report status changes with fields for origin/destination users, message content, type (enviado_para_aprovacao, aprovado, rejeitado), read status, and email delivery tracking.

## Key Features
- **Project Management**: CRUD operations, automatic numbering, GPS location, dynamic project categories.
- **Visit Tracking**: GPS-enabled logging, custom checklists, team communication.
- **Report System**: Professional PDF reports with photo annotation, ELP branding, and approval workflow.
- **Photo Management**: Advanced editing (drawing, arrows, text, captions), up to 50 photos per report, predefined caption management, deduplication via image hashing.
- **Client Email Management**: CRUD system for client emails per project.
- **Approval Workflow**: Admin approval for reports with automated notification system.
- **Internal Notifications System**: Complete notification system with database storage and automatic email alerts for report status changes (submitted for approval, approved, rejected).
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