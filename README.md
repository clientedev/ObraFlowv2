# 🏗️ ELP Consultoria - Sistema de Gestão de Vistorias e Relatórios

<div align="center">

![ELP Logo](static/logo_elp_navbar.png)

**Sistema Profissional Integrado para Gestão de Obras, Vistorias Técnicas e Relatórios**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3.svg)](https://getbootstrap.com/)

</div>

---

## 📋 Índice

- [Sobre o Sistema](#-sobre-o-sistema)
- [Funcionalidades Principais](#-funcionalidades-principais)
- [Módulos do Sistema](#-módulos-do-sistema)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Requisitos](#-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Segurança](#-segurança)
- [Integrações](#-integrações)
- [Suporte](#-suporte)

---

## 🎯 Sobre o Sistema

O **ELP Consultoria** é uma plataforma web completa desenvolvida para gestão profissional de obras, vistorias técnicas e relatórios de acompanhamento. Projetado para engenheiros, consultores e equipes de campo, o sistema oferece ferramentas robustas para documentação, rastreamento e comunicação em projetos de construção civil.

### Principais Diferenciais

✅ **Gestão Completa de Relatórios** - Relatórios padrão e express com editor de fotos integrado  
✅ **Calendário de Visitas** - Agendamento inteligente com notificações automáticas  
✅ **Geolocalização Avançada** - Registro preciso de coordenadas GPS em visitas  
✅ **Comunicação Integrada** - Sistema de notificações push e e-mail  
✅ **Backup Automático** - Integração com Google Drive  
✅ **Gestão Financeira** - Módulo completo de reembolsos e despesas  
✅ **Editor de Fotos Profissional** - Edição, anotações e legendas em imagens  

---

## 🚀 Funcionalidades Principais

### 📊 Gestão de Relatórios

#### Relatórios Padrão
- **Criação Completa**: Formulários detalhados com validação automática
- **Upload Múltiplo de Fotos**: Suporte ilimitado de imagens (até 3GB por relatório)
- **Editor de Fotos Integrado**: Canvas interativo com Fabric.js
  - Desenho livre, formas geométricas, textos
  - Filtros (preto e branco, sépia, blur, contraste)
  - Controle de brilho, saturação e exposição
  - Anotações e marcações personalizadas
- **Sistema de Legendas**: Legendas predefinidas e customizadas
- **Aprovação Multinível**: Fluxo de aprovação com múltiplos aprovadores
- **Exportação PDF**: Geração automática de relatórios em PDF profissional
- **Envio por E-mail**: Distribuição automática para clientes e aprovadores
- **Versionamento**: Histórico completo de alterações e reenvios

#### Relatórios Express
- **Criação Rápida**: Formulário simplificado para vistorias ágeis
- **Captura de Fotos**: Interface otimizada para dispositivos móveis
- **Edição em Tempo Real**: Modificação sem necessidade de reenvio
- **Compartilhamento Instantâneo**: Envio rápido por e-mail

### 📅 Calendário e Agendamento

- **Calendário Visual**: Interface interativa com FullCalendar
- **Agendamento de Visitas**: Programação com data/hora e responsáveis
- **Cores Personalizadas**: Identificação visual por tipo de visita
- **Notificações Automáticas**: Lembretes antes das visitas agendadas
- **Sincronização em Tempo Real**: Atualizações instantâneas para toda equipe
- **Histórico de Visitas**: Registro completo de todas as atividades

### 🏢 Gestão de Obras (Projetos)

- **Cadastro Completo**: Informações técnicas detalhadas
  - Dados cadastrais e contratuais
  - Informações técnicas de fachada
  - Especificações de materiais e acabamentos
  - Cores, texturas e revestimentos
- **Responsáveis e Equipes**: Atribuição de funcionários por projeto
- **Contatos Associados**: Gestão de clientes e stakeholders
- **Dashboard por Obra**: Visão consolidada de relatórios e visitas
- **Localização GPS**: Mapeamento de obras próximas
- **Documentação Técnica**: Armazenamento de especificações e normas

### 👥 Gestão de Usuários e Permissões

- **Níveis de Acesso**:
  - 🔴 **Master**: Acesso total e administrativo
  - 🔵 **Developer**: Acesso técnico e manutenção
  - 🟢 **Funcionário Padrão**: Acesso operacional
- **Autenticação Segura**: Sistema de login com criptografia
- **Recuperação de Senha**: Fluxo automatizado via e-mail
- **Perfis Personalizados**: Nome, cargo, telefone, foto
- **Rastreamento de Atividades**: Log de ações dos usuários

### 💰 Gestão Financeira

#### Reembolsos
- **Solicitação de Reembolso**: Formulário completo com anexos
- **Categorias**: Combustível, alimentação, transporte, outros
- **Upload de Comprovantes**: Anexo de notas fiscais e recibos
- **Aprovação Administrativa**: Painel master para aprovação/rejeição
- **Relatórios Financeiros**: Exportação de dados para contabilidade
- **Histórico Completo**: Consulta de reembolsos por período

### 🔔 Sistema de Notificações

- **Notificações Push**: OneSignal SDK integrado
- **Notificações Internas**: Central de notificações no sistema
- **E-mail Automatizado**: Envios via SMTP (Hostinger/Gmail)
- **Tipos de Notificação**:
  - Aprovação de relatórios
  - Novos relatórios designados
  - Lembretes de visitas
  - Atualização de projetos
  - Reembolsos aprovados/rejeitados
- **Preferências Personalizadas**: Controle de notificações por usuário
- **Badges e Contadores**: Indicadores visuais de novas notificações

### 📸 Editor de Fotos Avançado

- **Canvas Interativo**: Edição profissional com Fabric.js
- **Ferramentas de Desenho**:
  - Pincel livre com controle de espessura
  - Formas geométricas (retângulo, círculo, linha, seta)
  - Textos com fontes personalizadas
- **Filtros e Ajustes**:
  - Preto e branco, sépia, blur
  - Brilho, contraste, saturação
  - Exposição e gamma
- **Legendas Inteligentes**: Aplicação de legendas predefinidas
- **Histórico de Edição**: Desfazer/refazer ilimitado
- **Exportação**: Salvar edições em alta qualidade

### 🗂️ Gestão de Checklists

- **Templates Customizáveis**: Criação de modelos reutilizáveis
- **Categorização**: Organização por tipo de vistoria
- **Aplicação em Relatórios**: Integração automática em formulários
- **Versões**: Controle de diferentes versões de checklists

### 📧 Comunicação e E-mails

- **SMTP Configurável**: Suporte para múltiplos provedores
- **Templates Profissionais**: E-mails em HTML responsivos
- **Envio em Massa**: Distribuição para múltiplos destinatários
- **Rastreamento**: Log de e-mails enviados
- **Anexos**: Suporte para PDFs e imagens

### ☁️ Backup e Armazenamento

- **Google Drive Integration**: Backup automático de relatórios aprovados
- **Estrutura Organizada**: Pastas por cliente e projeto
- **Backup Manual**: Opção de backup forçado
- **Recuperação**: Restauração de documentos do Drive

### 📱 Interface Responsiva

- **Design Mobile-First**: Otimizado para tablets e smartphones
- **Temas**: Interface profissional com cores ELP
- **Acessibilidade**: Suporte para leitores de tela e navegação por teclado
- **PWA Ready**: Instalável como aplicativo nativo

---

## 🔧 Módulos do Sistema

### 1. **Módulo de Relatórios**
- `routes.py`: Rotas principais de relatórios
- `routes_relatorios_api.py`: API REST para operações
- `pdf_generator.py`: Geração de PDFs profissionais
- `templates/reports/`: Templates de visualização

### 2. **Módulo de Relatórios Express**
- `routes_express.py`: Lógica de relatórios rápidos
- `pdf_generator_express.py`: PDFs simplificados
- `templates/relatorios_express/`: Interface express

### 3. **Módulo de Visitas**
- Agendamento e calendário
- Geolocalização GPS
- Comunicação com obras

### 4. **Módulo de Projetos**
- Cadastro de obras
- Informações técnicas
- Gestão de equipes

### 5. **Módulo de Notificações**
- `notification_service.py`: Serviço de notificações
- `onesignal_service.py`: Integração OneSignal
- Push notifications

### 6. **Módulo de Autenticação**
- Login/Logout
- Recuperação de senha
- Gestão de sessões

### 7. **Módulo Financeiro**
- Reembolsos
- Aprovações
- Relatórios financeiros

### 8. **Módulo de Backup**
- `google_drive_backup.py`: Integração Google Drive
- Backup automático
- Recuperação de documentos

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.11+**: Linguagem principal
- **Flask 3.0**: Framework web
- **SQLAlchemy**: ORM para banco de dados
- **PostgreSQL**: Banco de dados relacional
- **Alembic**: Migrações de banco de dados
- **Gunicorn**: Servidor WSGI de produção

### Frontend
- **Bootstrap 5.3**: Framework CSS
- **Font Awesome 6.4**: Biblioteca de ícones
- **Fabric.js**: Editor de canvas para fotos
- **FullCalendar**: Calendário interativo
- **JavaScript ES6+**: Lógica client-side

### Integrações
- **OneSignal**: Notificações push
- **Google Drive API**: Backup em nuvem
- **SMTP (Hostinger/Gmail)**: Envio de e-mails
- **Geolocation API**: Localização GPS

### Infraestrutura
- **Railway**: Plataforma de deployment
- **Nixpacks**: Build e deployment automatizado
- **GitHub**: Controle de versão

---

## 📦 Requisitos

### Sistema Operacional
- Linux (Ubuntu 20.04+ recomendado)
- macOS 10.15+
- Windows 10/11 (com WSL2)

### Software Necessário
- Python 3.11 ou superior
- PostgreSQL 15 ou superior
- Git
- Node.js 18+ (opcional, para desenvolvimento frontend)

### Bibliotecas Python
Ver `requirements.txt` para lista completa. Principais:
```
Flask>=3.0.0
SQLAlchemy>=2.0.0
psycopg2-binary>=2.9.0
Pillow>=10.0.0
reportlab>=4.0.0
google-auth>=2.0.0
APScheduler>=3.10.0
```

---

## 🚀 Instalação

### 1. Clone o Repositório
```bash
git clone https://github.com/clientedev/ObraFlowv2.git
cd ObraFlowv2
```

### 2. Crie Ambiente Virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale Dependências
```bash
pip install -r requirements.txt
```

### 4. Configure Banco de Dados
```bash
# Crie banco PostgreSQL
createdb elp_obraflow

# Execute migrações
flask db upgrade
```

### 5. Configure Variáveis de Ambiente
Crie arquivo `.env` (veja `.env.example`):
```env
DATABASE_URL=postgresql://usuario:senha@localhost/elp_obraflow
SECRET_KEY=sua_chave_secreta_segura
ONESIGNAL_APP_ID=seu_onesignal_app_id
ONESIGNAL_REST_API_KEY=sua_rest_api_key
GOOGLE_DRIVE_CREDENTIALS=path/to/credentials.json
SMTP_SERVER=smtp.hostinger.com
SMTP_PORT=465
SMTP_USER=seu_email@dominio.com
SMTP_PASSWORD=sua_senha
```

### 6. Execute a Aplicação
```bash
# Desenvolvimento
python main.py

# Produção
gunicorn main:app --bind 0.0.0.0:8000 --workers 4
```

---

## ⚙️ Configuração

### Google Drive API
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto
3. Ative a Google Drive API
4. Crie credenciais (Service Account)
5. Baixe o arquivo JSON de credenciais
6. Configure o caminho em `.env`

### OneSignal Push Notifications
1. Crie conta em [OneSignal](https://onesignal.com/)
2. Crie um novo app Web Push
3. Obtenha App ID e REST API Key
4. Configure em `.env` e `base.html`

### SMTP E-mail
Configure seu provedor SMTP preferido:
- **Hostinger**: smtp.hostinger.com, porta 465
- **Gmail**: smtp.gmail.com, porta 587
- **Outros**: Consulte documentação do provedor

---

## 📁 Estrutura do Projeto

```
ObraFlowv2/
├── static/                 # Arquivos estáticos
│   ├── css/               # Estilos CSS
│   ├── js/                # JavaScript
│   ├── icons/             # Ícones PWA
│   └── uploads/           # Uploads de usuários
├── templates/             # Templates HTML (Jinja2)
│   ├── reports/           # Templates de relatórios
│   ├── projects/          # Templates de obras
│   └── base.html          # Template base
├── migrations/            # Migrações Alembic
├── models.py              # Modelos SQLAlchemy
├── routes.py              # Rotas principais
├── routes_express.py      # Rotas relatórios express
├── routes_relatorios_api.py # API de relatórios
├── pdf_generator.py       # Gerador de PDFs
├── notification_service.py # Serviço de notificações
├── google_drive_backup.py # Backup Google Drive
├── app.py                 # Configuração Flask
├── main.py                # Entry point
├── requirements.txt       # Dependências Python
└── README.md              # Este arquivo
```

---

## 🔒 Segurança

### Implementações de Segurança
- ✅ **CSRF Protection**: Flask-WTF com tokens CSRF
- ✅ **Password Hashing**: Bcrypt com salt
- ✅ **SQL Injection Prevention**: SQLAlchemy parametrizado
- ✅ **XSS Protection**: Sanitização automática de inputs
- ✅ **HTTPS**: Obrigatório em produção
- ✅ **Session Management**: Cookies seguros e httpOnly
- ✅ **Rate Limiting**: Proteção contra brute force

### Boas Práticas
- Senhas criptografadas no banco
- Validação de inputs server-side
- Logs de auditoria
- Backups automáticos
- Variáveis sensíveis em `.env`

---

## 🔗 Integrações

### OneSignal (Push Notifications)
```javascript
// Configuração em base.html
OneSignal.init({
    appId: "YOUR_APP_ID",
    serviceWorkerPath: "/OneSignalSDKWorker.js"
});
```

### Google Drive (Backup)
```python
# google_drive_backup.py
def backup_report_to_drive(report_id):
    # Gera PDF e envia para pasta específica no Drive
    pass
```

### SMTP (E-mail)
```python
# email_service.py
def send_report_email(recipients, report_pdf):
    # Envia e-mail com template profissional
    pass
```

---

## 📊 Fluxos de Trabalho

### Fluxo de Criação de Relatório
1. Usuário acessa `/reports/new`
2. Preenche formulário com dados da vistoria
3. Upload de fotos (múltiplas)
4. Edição de fotos com canvas
5. Aplicação de legendas
6. Salva como rascunho ou envia
7. Sistema gera PDF automaticamente
8. Notifica aprovadores via e-mail/push
9. Aprovadores avaliam e aprovam/rejeitam
10. Relatório aprovado → Backup no Google Drive
11. Cliente recebe automaticamente por e-mail

### Fluxo de Agendamento de Visita
1. Acessa calendário
2. Seleciona data/hora
3. Escolhe obra e responsável
4. Define tipo de visita
5. Sistema cria evento
6. Notificação para responsável
7. Lembrete automático próximo à data
8. Check-in com geolocalização
9. Criação de relatório vinculado

---

## 🎨 Personalização

### Cores e Tema
Edite `static/css/style.css`:
```css
:root {
    --elp-primary: #20c1e8;   /* Azul ELP */
    --elp-dark: #343a40;       /* Cinza escuro */
    --elp-success: #28a745;    /* Verde sucesso */
}
```

### Logos e Branding
Substitua arquivos em:
- `static/logo_elp_navbar.png` - Logo da navbar
- `static/icons/icon-*.png` - Ícones do app

---

## 🐛 Troubleshooting

### Erro de Conexão com Banco
```bash
# Verifique se PostgreSQL está rodando
sudo service postgresql status

# Teste conexão
psql -U usuario -d elp_obraflow
```

### Erro de Migração
```bash
# Limpe versões e reinicie
flask db stamp head
flask db migrate -m "Initial migration"
flask db upgrade
```

### Erro no Google Drive
- Verifique credenciais JSON
- Confirme permissões da Service Account
- Teste com `python google_drive_backup.py`

---

## 📞 Suporte

### Desenvolvedor
**GL Systems**  
🌐 Website: [gl-systems.pro](https://www.gl-systems.pro)  
📧 E-mail: contato@gl-systems.pro

### Documentação Adicional
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://www.sqlalchemy.org/)
- [Bootstrap 5](https://getbootstrap.com/docs/5.3/)
- [OneSignal Docs](https://documentation.onesignal.com/)

---

## 📄 Licença

Copyright © 2025 ELP Consultoria e Engenharia. Todos os direitos reservados.

Sistema desenvolvido exclusivamente para uso interno da ELP Consultoria.

---

<div align="center">

**🏗️ ELP Consultoria - Excelência em Gestão de Obras**

*Sistema profissional para relatórios técnicos e gestão de vistorias*

</div>
