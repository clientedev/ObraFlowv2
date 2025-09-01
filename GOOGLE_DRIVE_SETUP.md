# Configuração do Google Drive - Guia Completo

## 📋 Visão Geral
O sistema de backup automático suporta duas formas de autenticação com o Google Drive:
1. **OAuth 2.0** (recomendado para desenvolvimento)
2. **Service Account** (recomendado para produção)

## 🔧 Método 1: OAuth 2.0 (Mais Simples)

### Passo 1: Configurar no Google Cloud Console
1. Acesse: https://console.cloud.google.com/
2. Crie um novo projeto ou selecione um existente
3. Vá para "APIs & Services" > "Library"
4. Procure e ative a "Google Drive API"
5. Vá para "APIs & Services" > "Credentials"
6. Clique em "Create Credentials" > "OAuth 2.0 Client IDs"
7. Configure:
   - Application type: "Web application"
   - Name: "ELP Sistema Backup"
   - Authorized redirect URIs: adicione `https://developers.google.com/oauthplayground`

### Passo 2: Obter Token de Acesso
1. Acesse: https://developers.google.com/oauthplayground/
2. Clique no ícone de configurações (⚙️) no canto superior direito
3. Marque "Use your own OAuth credentials"
4. Insira seu Client ID e Client Secret
5. No lado esquerdo, em "Step 1", procure por "Drive API v3"
6. Selecione `https://www.googleapis.com/auth/drive`
7. Clique "Authorize APIs"
8. Faça login com sua conta Google
9. Clique "Exchange authorization code for tokens"
10. Copie o "Access token" gerado

### Passo 3: Configurar no Replit
1. No Replit, abra a aba "Secrets" (🔒) na barra lateral
2. Adicione uma nova secret:
   - Key: `GOOGLE_DRIVE_ACCESS_TOKEN`
   - Value: Cole o token obtido no passo anterior

## 🔐 Método 2: Service Account (Produção)

### Passo 1: Criar Service Account
1. No Google Cloud Console, vá para "IAM & Admin" > "Service Accounts"
2. Clique "Create Service Account"
3. Configure:
   - Service account name: "elp-drive-backup"
   - Description: "Backup automático de relatórios"
4. Clique "Create and Continue"
5. Pule as permissões (não necessário para este caso)
6. Clique "Done"

### Passo 2: Gerar Chave JSON
1. Clique na service account criada
2. Vá para a aba "Keys"
3. Clique "Add Key" > "Create new key"
4. Selecione "JSON" e clique "Create"
5. O arquivo JSON será baixado automaticamente

### Passo 3: Configurar no Replit
1. Abra o arquivo JSON baixado
2. Copie todo o conteúdo do arquivo
3. No Replit, abra a aba "Secrets" (🔒)
4. Adicione uma nova secret:
   - Key: `GOOGLE_SERVICE_ACCOUNT_JSON`
   - Value: Cole todo o conteúdo JSON (deve começar com `{"type": "service_account"...`)

### Passo 4: Compartilhar Pasta do Drive
1. Acesse a pasta do Google Drive: https://drive.google.com/drive/folders/1DasfSDL0832tx6AQcQGMFMlOm4JMboAx
2. Clique em "Compartilhar" (ícone de pessoa com +)
3. No arquivo JSON, encontre o campo "client_email" (ex: elp-drive-backup@project-name.iam.gserviceaccount.com)
4. Adicione este email com permissão de "Editor"
5. Clique "Enviar"

## 📱 Como Configurar as Secrets no Replit

### Via Interface Web:
1. Abra seu projeto no Replit
2. Na barra lateral esquerda, clique no ícone de "Secrets" (🔒)
3. Clique em "New Secret"
4. Preencha:
   - **Key**: `GOOGLE_DRIVE_ACCESS_TOKEN` ou `GOOGLE_SERVICE_ACCOUNT_JSON`
   - **Value**: Seu token/JSON
5. Clique "Add Secret"

### Via Shell (alternativo):
```bash
# Método não recomendado - use a interface web por segurança
export GOOGLE_DRIVE_ACCESS_TOKEN="seu_token_aqui"
```

## ✅ Testando a Configuração

Após configurar as credenciais:

1. **Via Interface Web**:
   - Faça login como usuário administrador
   - Vá no menu "Administração"
   - Clique em "Testar Google Drive"
   - Veja a mensagem de sucesso/erro

2. **Via Backup Manual**:
   - Acesse qualquer relatório aprovado
   - No menu administrativo, use "Backup Todos Relatórios"
   - Verifique se os arquivos aparecem na pasta do Google Drive

## 🚨 Solução de Problemas

### Token Expirou
- **Sintoma**: Erro "Token de acesso expirado"
- **Solução**: Gere um novo token no OAuth Playground e atualize a secret

### Service Account sem Acesso
- **Sintoma**: Erro "Acesso negado à pasta"
- **Solução**: Verifique se o email da service account foi adicionado à pasta compartilhada

### Secrets não Carregando
- **Sintoma**: Erro "Token não configurado"
- **Solução**: Verifique se o nome da secret está exato (maiúsculas/minúsculas importam)

## 📝 Notas Importantes

- **Segurança**: Nunca exponha tokens ou chaves JSON em código
- **Expiração**: Tokens OAuth expiram, service accounts não
- **Permissões**: A pasta precisa ter permissão de "Editor" para uploads
- **Backup**: Mantenha uma cópia segura das credenciais

## 🔄 Renovação de Token (OAuth)

Os tokens OAuth expiram. Para renová-los:
1. Use o refresh_token (se disponível) via API
2. Ou repita o processo do OAuth Playground
3. Atualize a secret no Replit

Para produção, recomenda-se usar Service Account que não expira.