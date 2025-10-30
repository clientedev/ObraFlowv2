# 🔥 Guia Completo de Configuração Firebase Cloud Messaging

## 📋 Visão Geral

Este guia detalha como configurar o sistema de **Push Notifications** com Firebase Cloud Messaging (FCM) no sistema ELP Consultoria.

### ✨ Funcionalidades Implementadas

- ✅ **Push Notifications em Background** - Funciona com app fechado
- ✅ **Notificações em Foreground** - Funciona com app aberto
- ✅ **Backend Firebase Admin SDK** - Envio de notificações do servidor
- ✅ **Frontend Firebase JS SDK** - Registro de tokens e recepção
- ✅ **Service Worker** - Gerenciamento de notificações em background
- ✅ **Expiração de 24h** - Notificações antigas são removidas automaticamente
- ✅ **Sistema Dual** - Notificações internas (banco de dados) + externas (FCM)

---

## 🚀 Passo 1: Criar Projeto Firebase

1. Acesse [Firebase Console](https://console.firebase.google.com/)
2. Clique em **"Adicionar projeto"** ou use um existente
3. Configure o nome do projeto (ex: `elp-consultoria-push`)
4. Aceite os termos e crie o projeto
5. Aguarde a criação (pode levar alguns minutos)

---

## 🔧 Passo 2: Configurar Cloud Messaging

1. No Firebase Console, acesse seu projeto
2. No menu lateral, clique em **"Cloud Messaging"**
3. Se solicitado, ative o **Cloud Messaging API**
4. Anote o **Sender ID** (você precisará dele)

---

## 🔐 Passo 3: Obter Credenciais do Backend

### Opção A: Arquivo JSON (Recomendado)

1. Firebase Console → **⚙️ Configurações** → **Contas de serviço**
2. Clique em **"Gerar nova chave privada"**
3. Será baixado um arquivo JSON (ex: `elp-consultoria-xxxx.json`)
4. **Renomeie** para `firebase_credentials.json`
5. **Coloque** na raiz do projeto (mesmo nível de `main.py`)
6. **Configure** variável de ambiente:
   ```bash
   FIREBASE_CREDENTIALS_PATH=firebase_credentials.json
   ```

### Opção B: Variável de Ambiente (Alternativa)

1. Abra o arquivo JSON baixado
2. **Copie TODO o conteúdo** (é um JSON completo)
3. Cole em uma variável de ambiente:
   ```bash
   FIREBASE_CONFIG='{"type":"service_account","project_id":"...","private_key":"...","client_email":"..."}'
   ```

---

## 🌐 Passo 4: Obter Configuração Web (Frontend)

1. Firebase Console → **⚙️ Configurações** → **Geral**
2. Role até **"Seus apps"**
3. Clique em **"Adicionar app"** → Selecione **Web** (ícone `</>`)
4. Dê um nome (ex: `ELP Web App`)
5. **Copie** as variáveis do `firebaseConfig`:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSy...",
  authDomain: "elp-consultoria.firebaseapp.com",
  projectId: "elp-consultoria",
  storageBucket: "elp-consultoria.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abc123"
};
```

6. **Configure** as variáveis de ambiente (.env ou Railway):

```bash
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN=elp-consultoria.firebaseapp.com
FIREBASE_PROJECT_ID=elp-consultoria
FIREBASE_STORAGE_BUCKET=elp-consultoria.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789012
FIREBASE_APP_ID=1:123456789012:web:abc123
```

---

## 🔑 Passo 5: Gerar VAPID Key

1. Firebase Console → **⚙️ Configurações** → **Cloud Messaging**
2. Role até **"Configuração da Web"**
3. Clique em **"Gerar par de chaves"** (se ainda não tiver)
4. **Copie** a "Chave do servidor web" (começa com `B...`)
5. Configure a variável:
   ```bash
   FIREBASE_VAPID_KEY=BNabc123def456...
   ```

---

## 📝 Passo 6: Configurar Service Worker

1. Abra o arquivo `static/firebase-messaging-sw.js`
2. **Substitua** os valores `YOUR_*` pelos valores reais:

```javascript
const firebaseConfig = {
    apiKey: "AIzaSy...",           // Seu valor real
    authDomain: "elp-consultoria.firebaseapp.com",
    projectId: "elp-consultoria",
    storageBucket: "elp-consultoria.appspot.com",
    messagingSenderId: "123456789012",
    appId: "1:123456789012:web:abc123"
};
```

3. **Salve** o arquivo

---

## 🎨 Passo 7: Integrar no Frontend

### Opção A: HTML Template (Recomendado)

Adicione no `<head>` do seu template base (ex: `base.html`):

```html
<!-- Firebase Push Notifications -->
<script type="module">
  import FirebaseNotificationsManager from '/static/js/firebase-notifications.js';
  
  // Configuração Firebase (use variáveis do backend)
  const firebaseConfig = {
    apiKey: "{{ config.FIREBASE_API_KEY }}",
    authDomain: "{{ config.FIREBASE_AUTH_DOMAIN }}",
    projectId: "{{ config.FIREBASE_PROJECT_ID }}",
    storageBucket: "{{ config.FIREBASE_STORAGE_BUCKET }}",
    messagingSenderId: "{{ config.FIREBASE_MESSAGING_SENDER_ID }}",
    appId: "{{ config.FIREBASE_APP_ID }}"
  };
  
  const vapidKey = "{{ config.FIREBASE_VAPID_KEY }}";
  
  // Inicializar quando página carregar
  document.addEventListener('DOMContentLoaded', async () => {
    const fcmManager = new FirebaseNotificationsManager();
    
    if (await fcmManager.initialize(firebaseConfig)) {
      console.log('✅ Firebase inicializado');
      
      // Solicitar permissão automaticamente após login
      // ou criar botão para usuário ativar
      const token = await fcmManager.requestPermissionAndGetToken(vapidKey);
      
      if (token) {
        console.log('✅ Push notifications ativadas');
      }
    }
  });
</script>
```

### Opção B: Botão de Ativação (Recomendado para UX)

```html
<button id="enablePushBtn" class="btn btn-primary">
  🔔 Ativar Notificações Push
</button>

<script type="module">
  import FirebaseNotificationsManager from '/static/js/firebase-notifications.js';
  
  const fcmManager = new FirebaseNotificationsManager();
  await fcmManager.initialize(firebaseConfig);
  
  document.getElementById('enablePushBtn').addEventListener('click', async () => {
    const token = await fcmManager.requestPermissionAndGetToken(vapidKey);
    
    if (token) {
      alert('✅ Notificações ativadas com sucesso!');
    } else {
      alert('❌ Não foi possível ativar notificações');
    }
  });
</script>
```

---

## 🖥️ Passo 8: Enviar Notificações do Backend

### Exemplo de Uso em Python (routes.py):

```python
from firebase_utils import send_push_notification
from models import User

# Enviar para um usuário específico
user = User.query.filter_by(username='admin').first()

send_push_notification(
    user=user,
    title="Novo Relatório Aprovado",
    body="O relatório #123 foi aprovado com sucesso!",
    data={
        'url': '/relatorio/123',
        'tag': 'relatorio-aprovado'
    },
    image_url='https://seu-dominio.com/imagem.png'  # Opcional
)
```

### Enviar para Múltiplos Usuários:

```python
from firebase_utils import send_push_notification_multiple
from models import User

users = User.query.filter(User.fcm_token.isnot(None)).all()

result = send_push_notification_multiple(
    users=users,
    title="Manutenção Programada",
    body="O sistema ficará fora do ar hoje à noite das 23h às 01h",
    data={'url': '/avisos'}
)

print(f"✅ Enviadas: {result['sent']}, ❌ Falhas: {result['failed']}")
```

---

## 🧪 Passo 9: Testar Sistema

### Teste 1: Backend Initialization

```bash
# Execute o Flask e verifique os logs
python main.py

# Procure por:
# ✅ Firebase FCM inicializado com sucesso
```

### Teste 2: Frontend Token Registration

1. Abra o navegador com DevTools (F12)
2. Acesse a aplicação
3. Clique no botão de ativar notificações
4. No console, procure:
   ```
   ✅ FCM Token obtido: ...
   ✅ Token salvo no servidor com sucesso
   ```

### Teste 3: Banco de Dados

```sql
-- Verificar se token foi salvo
SELECT id, username, fcm_token FROM users WHERE fcm_token IS NOT NULL;
```

### Teste 4: Envio Manual via cURL

```bash
curl -X POST https://fcm.googleapis.com/fcm/send \
  -H "Authorization: key=YOUR_SERVER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "USER_FCM_TOKEN_FROM_DATABASE",
    "notification": {
      "title": "Teste ELP",
      "body": "Push notification funcionando!"
    }
  }'
```

### Teste 5: Envio via Python

```python
# No shell do Python:
from app import app
from models import User
from firebase_utils import send_push_notification

with app.app_context():
    user = User.query.first()
    send_push_notification(
        user=user,
        title="Teste",
        body="Testando push notification"
    )
```

---

## 📊 Estrutura de Arquivos

```
/
├── app.py                          # Inicializa Firebase na inicialização
├── firebase_utils.py               # Funções de envio (backend)
├── firebase_credentials.json       # Credenciais Firebase (NÃO COMMITAR!)
├── routes.py                       # Endpoint /api/update_fcm_token
├── models.py                       # Campo fcm_token no User
├── static/
│   ├── firebase-messaging-sw.js   # Service Worker FCM
│   └── js/
│       └── firebase-notifications.js  # Manager Frontend
└── templates/
    └── base.html                  # Integração HTML
```

---

## 🔒 Segurança

### ⚠️ NUNCA Commitar Credenciais

Adicione ao `.gitignore`:

```gitignore
firebase_credentials.json
.env
```

### ✅ Usar Variáveis de Ambiente

No Railway/Replit, configure as variáveis sem commitar arquivos:

```bash
# Backend (privado)
FIREBASE_CREDENTIALS_PATH=firebase_credentials.json
# ou
FIREBASE_CONFIG='{"type":"service_account",...}'

# Frontend (público - OK expor)
FIREBASE_API_KEY=...
FIREBASE_PROJECT_ID=...
```

---

## 🐛 Troubleshooting

### Problema: "Firebase não inicializado"

**Solução:**
1. Verifique se `firebase_credentials.json` existe
2. Verifique permissões do arquivo
3. Verifique variável `FIREBASE_CREDENTIALS_PATH`

### Problema: "Token não salvo"

**Solução:**
1. Verifique se o usuário está logado
2. Verifique endpoint `/api/update_fcm_token`
3. Verifique logs do browser (F12 → Console)

### Problema: "Notificações não aparecem"

**Solução:**
1. Verifique permissão do navegador (deve estar "granted")
2. Verifique se service worker está registrado (DevTools → Application → Service Workers)
3. Teste com navegador em modo anônimo (sem extensões)
4. Certifique-se de que o app está em HTTPS

### Problema: "Firebase Admin erro de autenticação"

**Solução:**
1. Verifique se JSON está bem formado
2. Verifique se a conta de serviço tem permissões corretas
3. Redownload credenciais do Firebase Console

---

## 📚 Referências

- [Firebase Cloud Messaging Docs](https://firebase.google.com/docs/cloud-messaging)
- [Firebase Admin Python SDK](https://firebase.google.com/docs/admin/setup)
- [Firebase JS SDK](https://firebase.google.com/docs/web/setup)
- [Service Workers MDN](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)

---

## ✅ Checklist de Configuração

- [ ] Projeto Firebase criado
- [ ] Cloud Messaging ativado
- [ ] Credenciais backend obtidas (`firebase_credentials.json`)
- [ ] Configuração web obtida (firebaseConfig)
- [ ] VAPID Key gerada
- [ ] Service worker configurado
- [ ] Variáveis de ambiente definidas
- [ ] Frontend integrado
- [ ] Testado envio de notificação
- [ ] Credenciais adicionadas ao .gitignore

---

**🎉 Após completar todos os passos, seu sistema estará pronto para enviar push notifications!**
