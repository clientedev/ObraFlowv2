#!/bin/bash
# Script de deployment robusto para Railway
set -e

echo "🚀 INICIANDO DEPLOYMENT RAILWAY ULTRA-ROBUSTO"

# Atualizar pip primeiro
pip install --upgrade pip setuptools wheel

# Instalar dependências essenciais primeiro
echo "📦 Instalando dependências base..."
pip install Flask==3.1.1
pip install Flask-SQLAlchemy==3.1.1
pip install psycopg2-binary==2.9.10
pip install gunicorn==23.0.0

# Instalar dependências de segurança e forms
echo "🔐 Instalando dependências de segurança..."
pip install Flask-Login==0.6.3
pip install Flask-WTF==1.2.2
pip install WTForms==3.2.1
pip install Flask-Mail==0.10.0

# Instalar dependências de processamento
echo "🎨 Instalando dependências de processamento..."
pip install Pillow==11.3.0
pip install reportlab==4.4.3
pip install weasyprint==66.0

# Instalar dependências finais
echo "⚡ Instalando dependências finais..."
pip install requests==2.32.4
pip install email-validator==2.2.0
pip install PyJWT==2.10.1

echo "✅ TODAS DEPENDÊNCIAS INSTALADAS COM SUCESSO"

# Iniciar aplicação
echo "🚀 INICIANDO APLICAÇÃO..."
gunicorn main:app --bind 0.0.0.0:$PORT --workers 1 --timeout 300