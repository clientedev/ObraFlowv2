"""
Sistema de Backup Automático para Google Drive
Implementa upload seguro de relatórios e imagens para pasta compartilhada
"""

import os
import io
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

from flask import current_app, url_for, session, request, redirect, flash
from werkzeug.utils import secure_filename

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleDriveService:
    """Serviço para integração com Google Drive API"""
    
    # ID da pasta compartilhada fornecida pelo usuário
    SHARED_FOLDER_ID = "1DasfSDL0832tx6AQcQGMFMlOm4JMboAx"
    
    # Escopos necessários para o Google Drive
    SCOPES = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.folder'
    ]
    
    def __init__(self):
        self.service = None
        self.credentials = None
        
    def _get_credentials_from_env(self) -> Optional[Dict]:
        """Recupera credenciais do Google Drive das variáveis de ambiente"""
        try:
            client_id = os.environ.get('GOOGLE_DRIVE_CLIENT_ID')
            client_secret = os.environ.get('GOOGLE_DRIVE_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                logger.warning("Credenciais do Google Drive não encontradas nas variáveis de ambiente")
                return None
                
            return {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
                }
            }
        except Exception as e:
            logger.error(f"Erro ao recuperar credenciais: {e}")
            return None
    
    def get_authorization_url(self, redirect_uri: str) -> Optional[str]:
        """Gera URL de autorização OAuth 2.0 para o Google Drive"""
        try:
            credentials_info = self._get_credentials_from_env()
            if not credentials_info:
                return None
                
            # Atualizar redirect_uri nas credenciais
            credentials_info["web"]["redirect_uris"] = [redirect_uri]
            
            flow = Flow.from_client_config(
                credentials_info,
                scopes=self.SCOPES,
                redirect_uri=redirect_uri
            )
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            # Salvar estado na sessão
            session['oauth_state'] = state
            
            return authorization_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar URL de autorização: {e}")
            return None
    
    def handle_oauth_callback(self, authorization_code: str, redirect_uri: str) -> bool:
        """Processa callback OAuth e salva tokens"""
        try:
            credentials_info = self._get_credentials_from_env()
            if not credentials_info:
                return False
                
            credentials_info["web"]["redirect_uris"] = [redirect_uri]
            
            flow = Flow.from_client_config(
                credentials_info,
                scopes=self.SCOPES,
                redirect_uri=redirect_uri
            )
            
            # Verificar estado
            state = session.get('oauth_state')
            if not state:
                logger.error("Estado OAuth não encontrado na sessão")
                return False
            
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            # Salvar credenciais na sessão (em produção, usar banco de dados)
            session['google_drive_token'] = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': getattr(credentials, 'token_uri', 'https://oauth2.googleapis.com/token'),
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            self.credentials = credentials
            self._build_service()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro no callback OAuth: {e}")
            return False
    
    def _load_credentials_from_session(self) -> bool:
        """Carrega credenciais salvas da sessão"""
        try:
            token_data = session.get('google_drive_token')
            if not token_data:
                return False
                
            self.credentials = Credentials(
                token=token_data['token'],
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data['token_uri'],
                client_id=token_data['client_id'],
                client_secret=token_data['client_secret'],
                scopes=token_data['scopes']
            )
            
            # Verificar se o token precisa ser atualizado
            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                # Atualizar token na sessão
                session['google_drive_token']['token'] = self.credentials.token
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar credenciais da sessão: {e}")
            return False
    
    def _build_service(self):
        """Constrói o serviço do Google Drive"""
        try:
            if self.credentials:
                self.service = build('drive', 'v3', credentials=self.credentials)
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao construir serviço Google Drive: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Verifica se o usuário está autenticado no Google Drive"""
        if not self._load_credentials_from_session():
            return False
        return self._build_service()
    
    def create_project_folder(self, project_name: str, project_number: str) -> Optional[str]:
        """Cria pasta para o projeto dentro da pasta compartilhada"""
        try:
            if not self.is_authenticated():
                return None
                
            folder_name = f"{project_number} - {project_name}"
            
            # Verificar se a pasta já existe
            existing_folder = self._find_folder_by_name(folder_name, self.SHARED_FOLDER_ID)
            if existing_folder:
                return existing_folder['id']
            
            # Criar nova pasta
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [self.SHARED_FOLDER_ID]
            }
            
            if self.service:
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                logger.info(f"Pasta criada no Google Drive: {folder_name} (ID: {folder.get('id')})")
                return folder.get('id')
            else:
                logger.error("Serviço Google Drive não inicializado")
                return None
            
        except HttpError as e:
            logger.error(f"Erro HTTP ao criar pasta: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao criar pasta do projeto: {e}")
            return None
    
    def _find_folder_by_name(self, folder_name: str, parent_id: str) -> Optional[Dict]:
        """Encontra pasta pelo nome dentro de um diretório pai"""
        try:
            if not self.service:
                return None
                
            query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            folders = results.get('files', [])
            
            return folders[0] if folders else None
            
        except Exception as e:
            logger.error(f"Erro ao buscar pasta: {e}")
            return None
    
    def upload_file(self, file_path: str, filename: str, project_folder_id: str, 
                   mime_type: str = None) -> Optional[str]:
        """Faz upload de um arquivo para o Google Drive"""
        try:
            if not self.is_authenticated():
                logger.error("Não autenticado no Google Drive")
                return None
                
            if not os.path.exists(file_path):
                logger.error(f"Arquivo não encontrado: {file_path}")
                return None
            
            # Detectar tipo MIME se não fornecido
            if not mime_type:
                if filename.lower().endswith('.pdf'):
                    mime_type = 'application/pdf'
                elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    mime_type = 'image/jpeg' if filename.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
                else:
                    mime_type = 'application/octet-stream'
            
            # Preparar metadados do arquivo
            file_metadata = {
                'name': filename,
                'parents': [project_folder_id]
            }
            
            # Ler arquivo
            with open(file_path, 'rb') as file_content:
                media = MediaIoBaseUpload(
                    io.BytesIO(file_content.read()),
                    mimetype=mime_type,
                    resumable=True
                )
            
            # Upload do arquivo
            if not self.service:
                logger.error("Serviço Google Drive não inicializado")
                return None
                
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,createdTime'
            ).execute()
            
            file_id = file.get('id')
            file_size = file.get('size', 0)
            
            logger.info(f"Arquivo enviado para Google Drive: {filename} "
                       f"(ID: {file_id}, Tamanho: {file_size} bytes)")
            
            return file_id
            
        except HttpError as e:
            logger.error(f"Erro HTTP no upload: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao fazer upload do arquivo: {e}")
            return None
    
    def upload_from_bytes(self, file_bytes: bytes, filename: str, project_folder_id: str,
                         mime_type: str = None) -> Optional[str]:
        """Faz upload de arquivo a partir de bytes"""
        try:
            if not self.is_authenticated():
                return None
            
            if not mime_type:
                if filename.lower().endswith('.pdf'):
                    mime_type = 'application/pdf'
                elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    mime_type = 'image/jpeg' if filename.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
                else:
                    mime_type = 'application/octet-stream'
            
            file_metadata = {
                'name': filename,
                'parents': [project_folder_id]
            }
            
            media = MediaIoBaseUpload(
                io.BytesIO(file_bytes),
                mimetype=mime_type,
                resumable=True
            )
            
            if not self.service:
                logger.error("Serviço Google Drive não inicializado")
                return None
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size'
            ).execute()
            
            logger.info(f"Arquivo enviado (bytes): {filename} (ID: {file.get('id')})")
            return file.get('id')
            
        except Exception as e:
            logger.error(f"Erro ao fazer upload de bytes: {e}")
            return None
    
    def backup_project_files(self, project_id: int) -> Dict[str, Any]:
        """Faz backup de todos os arquivos de um projeto"""
        try:
            from models import Projeto, Relatorio, FotoRelatorio, RelatorioExpress, FotoRelatorioExpress
            
            # Buscar projeto
            projeto = Projeto.query.get(project_id)
            if not projeto:
                return {'success': False, 'error': 'Projeto não encontrado'}
            
            # Criar pasta do projeto
            project_folder_id = self.create_project_folder(projeto.nome, projeto.numero)
            if not project_folder_id:
                return {'success': False, 'error': 'Erro ao criar pasta do projeto'}
            
            results = {
                'success': True,
                'project_folder_id': project_folder_id,
                'uploaded_files': [],
                'errors': []
            }
            
            # Backup de relatórios PDF normais
            relatorios = Relatorio.query.filter_by(projeto_id=project_id).all()
            for relatorio in relatorios:
                try:
                    # Gerar PDF do relatório usando WeasyPrint
                    from pdf_generator_weasy import gerar_pdf_weasy
                    pdf_content = gerar_pdf_weasy(relatorio.id)
                    
                    if pdf_content:
                        filename = f"Relatorio_{relatorio.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        file_id = self.upload_from_bytes(pdf_content, filename, project_folder_id)
                        
                        if file_id:
                            results['uploaded_files'].append({
                                'type': 'relatorio',
                                'filename': filename,
                                'file_id': file_id,
                                'relatorio_id': relatorio.id
                            })
                        else:
                            results['errors'].append(f"Erro ao enviar relatório {relatorio.id}")
                            
                except Exception as e:
                    results['errors'].append(f"Erro ao processar relatório {relatorio.id}: {str(e)}")
            
            # Backup de relatórios Express
            relatorios_express = RelatorioExpress.query.filter_by(projeto_id=project_id).all()
            for relatorio in relatorios_express:
                try:
                    from pdf_generator_express import gerar_pdf_relatorio_express
                    pdf_content = gerar_pdf_relatorio_express(relatorio.id)
                    
                    if pdf_content:
                        filename = f"RelatorioExpress_{relatorio.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        file_id = self.upload_from_bytes(pdf_content, filename, project_folder_id)
                        
                        if file_id:
                            results['uploaded_files'].append({
                                'type': 'relatorio_express',
                                'filename': filename,
                                'file_id': file_id,
                                'relatorio_express_id': relatorio.id
                            })
                        else:
                            results['errors'].append(f"Erro ao enviar relatório express {relatorio.id}")
                            
                except Exception as e:
                    results['errors'].append(f"Erro ao processar relatório express {relatorio.id}: {str(e)}")
            
            # Backup de fotos de relatórios normais
            fotos = FotoRelatorio.query.join(Relatorio).filter(Relatorio.projeto_id == project_id).all()
            for foto in fotos:
                try:
                    foto_path = os.path.join('uploads', foto.arquivo)
                    if os.path.exists(foto_path):
                        filename = f"Foto_{foto.id}_{secure_filename(foto.arquivo)}"
                        file_id = self.upload_file(foto_path, filename, project_folder_id)
                        
                        if file_id:
                            results['uploaded_files'].append({
                                'type': 'foto',
                                'filename': filename,
                                'file_id': file_id,
                                'foto_id': foto.id
                            })
                        else:
                            results['errors'].append(f"Erro ao enviar foto {foto.id}")
                            
                except Exception as e:
                    results['errors'].append(f"Erro ao processar foto {foto.id}: {str(e)}")
            
            # Backup de fotos de relatórios express
            fotos_express = FotoRelatorioExpress.query.join(RelatorioExpress).filter(RelatorioExpress.projeto_id == project_id).all()
            for foto in fotos_express:
                try:
                    foto_path = os.path.join('uploads', foto.arquivo)
                    if os.path.exists(foto_path):
                        filename = f"FotoExpress_{foto.id}_{secure_filename(foto.arquivo)}"
                        file_id = self.upload_file(foto_path, filename, project_folder_id)
                        
                        if file_id:
                            results['uploaded_files'].append({
                                'type': 'foto_express',
                                'filename': filename,
                                'file_id': file_id,
                                'foto_express_id': foto.id
                            })
                        else:
                            results['errors'].append(f"Erro ao enviar foto express {foto.id}")
                            
                except Exception as e:
                    results['errors'].append(f"Erro ao processar foto express {foto.id}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Erro no backup do projeto: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Retorna status da configuração de backup"""
        return {
            'is_configured': self._get_credentials_from_env() is not None,
            'is_authenticated': self.is_authenticated(),
            'shared_folder_id': self.SHARED_FOLDER_ID
        }

# Instância global do serviço
drive_service = GoogleDriveService()