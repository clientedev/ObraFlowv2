"""
Sistema de backup automático para Google Drive
Integração com OAuth 2.0 para salvar relatórios em pastas organizadas
"""

import os
import io
import json
import tempfile
from datetime import datetime
from typing import Optional, List, Dict, Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveBackupOAuth:
    """Sistema de backup para Google Drive usando OAuth 2.0"""
    
    def __init__(self):
        self.credentials = None
        self.service = None
        
    def get_oauth_flow(self, redirect_uri: str) -> Flow:
        """
        Criar flow de autenticação OAuth 2.0
        
        Args:
            redirect_uri: URL de callback após autenticação
            
        Returns:
            Flow object para autenticação
        """
        client_config = self._get_client_config()
        
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        return flow
    
    def _get_client_config(self) -> Dict:
        """Obter configuração do cliente OAuth"""
        credentials_json = os.environ.get('GOOGLE_OAUTH_CREDENTIALS_JSON')
        
        if not credentials_json:
            raise Exception("GOOGLE_OAUTH_CREDENTIALS_JSON não configurado")
        
        return json.loads(credentials_json)
    
    def authorize_with_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Trocar código de autorização por tokens
        
        Args:
            code: Código de autorização do Google
            redirect_uri: URL de callback
            
        Returns:
            Token de acesso e refresh token (sem secrets sensíveis)
        """
        flow = self.get_oauth_flow(redirect_uri)
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
    
    def set_credentials_from_token(self, token_info: Dict[str, Any]):
        """
        Configurar credenciais a partir de token salvo
        
        Args:
            token_info: Dicionário com informações do token
        """
        client_config = self._get_client_config()
        web_config = client_config.get('web', {})
        
        self.credentials = Credentials(
            token=token_info.get('token'),
            refresh_token=token_info.get('refresh_token'),
            token_uri=web_config.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=web_config.get('client_id'),
            client_secret=web_config.get('client_secret'),
            scopes=SCOPES
        )
        
        self.service = build('drive', 'v3', credentials=self.credentials)
    
    def clear_credentials(self):
        """Limpar credenciais armazenadas"""
        self.credentials = None
        self.service = None
    
    def find_or_create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """
        Encontrar ou criar pasta no Drive
        
        Args:
            folder_name: Nome da pasta
            parent_id: ID da pasta pai (opcional)
            
        Returns:
            ID da pasta
        """
        if not self.service:
            raise Exception("Serviço não inicializado. Faça login primeiro.")
        
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            return files[0]['id']
        
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = self.service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        return folder.get('id')
    
    def list_files_in_folder(self, folder_id: str) -> List[str]:
        """
        Listar nomes de arquivos em uma pasta
        
        Args:
            folder_id: ID da pasta
            
        Returns:
            Lista de nomes de arquivos
        """
        if not self.service:
            return []
        
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(name)',
                pageSize=1000
            ).execute()
            
            files = results.get('files', [])
            return [f['name'] for f in files]
        except Exception as e:
            print(f"Erro ao listar arquivos: {e}")
            return []
    
    def file_exists_in_folder(self, filename: str, folder_id: str) -> bool:
        """
        Verificar se arquivo existe na pasta
        
        Args:
            filename: Nome do arquivo
            folder_id: ID da pasta
            
        Returns:
            True se existe
        """
        if not self.service:
            return False
        
        try:
            query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id)'
            ).execute()
            
            return len(results.get('files', [])) > 0
        except Exception as e:
            print(f"Erro ao verificar arquivo: {e}")
            return False
    
    def upload_pdf_bytes(self, pdf_bytes: bytes, filename: str, folder_id: str) -> Dict[str, Any]:
        """
        Upload de PDF em bytes para o Drive
        
        Args:
            pdf_bytes: Conteúdo do PDF em bytes
            filename: Nome do arquivo
            folder_id: ID da pasta de destino
            
        Returns:
            Informações do arquivo enviado
        """
        if not self.service:
            raise Exception("Serviço não inicializado. Faça login primeiro.")
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaIoBaseUpload(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            resumable=True
        )
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()
        
        return {
            'id': file.get('id'),
            'name': file.get('name'),
            'link': file.get('webViewLink')
        }
    
    def upload_file(self, file_path: str, folder_id: str, filename: str = None) -> Dict[str, Any]:
        """
        Upload de arquivo para o Drive
        
        Args:
            file_path: Caminho do arquivo local
            folder_id: ID da pasta de destino
            filename: Nome do arquivo (opcional)
            
        Returns:
            Informações do arquivo enviado
        """
        if not self.service:
            raise Exception("Serviço não inicializado. Faça login primeiro.")
        
        if not os.path.exists(file_path):
            raise Exception(f"Arquivo não encontrado: {file_path}")
        
        if not filename:
            filename = os.path.basename(file_path)
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(file_path, resumable=True)
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()
        
        return {
            'id': file.get('id'),
            'name': file.get('name'),
            'link': file.get('webViewLink')
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testar conexão com Google Drive
        
        Returns:
            Status da conexão
        """
        if not self.service:
            return {
                'success': False,
                'message': 'Não autenticado. Faça login primeiro.'
            }
        
        try:
            about = self.service.about().get(fields='user').execute()
            user = about.get('user', {})
            
            return {
                'success': True,
                'message': f"Conectado como: {user.get('displayName', 'Usuário')} ({user.get('emailAddress', '')})",
                'user': user
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro na conexão: {str(e)}'
            }


drive_backup = GoogleDriveBackupOAuth()


def get_authorization_url(redirect_uri: str) -> str:
    """
    Obter URL de autorização do Google
    
    Args:
        redirect_uri: URL de callback
        
    Returns:
        URL para redirecionar o usuário
    """
    flow = drive_backup.get_oauth_flow(redirect_uri)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    return authorization_url, state


def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Trocar código por token
    
    Args:
        code: Código de autorização
        redirect_uri: URL de callback
        
    Returns:
        Informações do token
    """
    return drive_backup.authorize_with_code(code, redirect_uri)


def backup_all_reports_to_drive(token_info: Dict[str, Any], db_session, Relatorio, FotoRelatorio, RelatorioExpress, FotoRelatorioExpress, WeasyPrintReportGenerator) -> Dict[str, Any]:
    """
    Fazer backup de todos os relatórios para o Google Drive
    
    Args:
        token_info: Token de autenticação
        db_session: Sessão do banco de dados
        Relatorio: Model de relatório
        FotoRelatorio: Model de fotos
        RelatorioExpress: Model de relatório express
        FotoRelatorioExpress: Model de fotos express
        WeasyPrintReportGenerator: Gerador de PDF
        
    Returns:
        Resultado do backup
    """
    backup_instance = GoogleDriveBackupOAuth()
    backup_instance.set_credentials_from_token(token_info)
    
    relatorio_folder_id = backup_instance.find_or_create_folder('Relatorio')
    express_folder_id = backup_instance.find_or_create_folder('Relatorio Express')
    
    results = {
        'relatorios': {'total': 0, 'success': 0, 'failed': 0, 'files': []},
        'express': {'total': 0, 'success': 0, 'failed': 0, 'files': []}
    }
    
    generator = WeasyPrintReportGenerator()
    
    # Usar case-insensitive para capturar todas as variações de status
    from sqlalchemy import func
    relatorios = Relatorio.query.filter(
        func.lower(Relatorio.status).in_(['aprovado', 'finalizado', 'aprovado final'])
    ).all()
    results['relatorios']['total'] = len(relatorios)
    
    # Obter lista de arquivos existentes na pasta para verificar duplicados
    existing_files_relatorio = backup_instance.list_files_in_folder(relatorio_folder_id)
    
    # Adicionar contadores de duplicados
    results['relatorios']['skipped'] = 0
    results['express']['skipped'] = 0
    
    for relatorio in relatorios:
        try:
            projeto_nome = relatorio.projeto.nome if relatorio.projeto else 'Sem_Projeto'
            projeto_nome = ''.join(c for c in projeto_nome if c.isalnum() or c in (' ', '-', '_'))[:50]
            
            # Usar nome base para verificar duplicados (sem data)
            filename_base = f"Relatorio_{relatorio.numero.replace('/', '_')}_{projeto_nome}"
            
            # Verificar se já existe um arquivo com este nome base
            duplicado = any(f.startswith(filename_base) for f in existing_files_relatorio)
            
            if duplicado:
                print(f"⏭️ Relatório {relatorio.numero} já existe no Drive - pulando")
                results['relatorios']['skipped'] += 1
                continue
            
            fotos = FotoRelatorio.query.filter_by(relatorio_id=relatorio.id).order_by(FotoRelatorio.ordem).all()
            
            pdf_bytes = generator.generate_report_pdf(relatorio, fotos)
            
            filename = f"{filename_base}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            file_info = backup_instance.upload_pdf_bytes(pdf_bytes, filename, relatorio_folder_id)
            
            results['relatorios']['success'] += 1
            results['relatorios']['files'].append({
                'numero': relatorio.numero,
                'filename': filename,
                'link': file_info.get('link')
            })
            
        except Exception as e:
            results['relatorios']['failed'] += 1
            print(f"Erro ao fazer backup do relatório {relatorio.id}: {str(e)}")
    
    # Usar case-insensitive para capturar todas as variações de status
    relatorios_express = RelatorioExpress.query.filter(
        func.lower(RelatorioExpress.status).in_(['aprovado', 'finalizado', 'aprovado final'])
    ).all()
    results['express']['total'] = len(relatorios_express)
    
    # Obter lista de arquivos existentes na pasta para verificar duplicados
    existing_files_express = backup_instance.list_files_in_folder(express_folder_id)
    
    # Importar função de geração de PDF Express (mesma usada no botão "Baixar PDF")
    from pdf_generator_express import gerar_pdf_relatorio_express
    
    for express in relatorios_express:
        try:
            obra_nome = express.obra_nome or 'Express'
            obra_nome = ''.join(c for c in obra_nome if c.isalnum() or c in (' ', '-', '_'))[:50]
            
            # Usar nome base para verificar duplicados (sem data)
            filename_base = f"Express_{express.numero.replace('/', '_')}_{obra_nome}"
            
            # Verificar se já existe um arquivo com este nome base
            duplicado = any(f.startswith(filename_base) for f in existing_files_express)
            
            if duplicado:
                print(f"⏭️ Relatório Express {express.numero} já existe no Drive - pulando")
                results['express']['skipped'] += 1
                continue
            
            # Usar a mesma função de geração de PDF do botão "Baixar PDF"
            pdf_result = gerar_pdf_relatorio_express(express.id, salvar_arquivo=False)
            
            # Verificar se retornou bytes ou BytesIO
            if hasattr(pdf_result, 'read'):
                pdf_bytes = pdf_result.read()
            elif isinstance(pdf_result, bytes):
                pdf_bytes = pdf_result
            else:
                raise Exception(f"Formato de PDF inesperado: {type(pdf_result)}")
            
            filename = f"{filename_base}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            file_info = backup_instance.upload_pdf_bytes(pdf_bytes, filename, express_folder_id)
            
            results['express']['success'] += 1
            results['express']['files'].append({
                'numero': express.numero,
                'filename': filename,
                'link': file_info.get('link')
            })
            
            print(f"✅ Relatório Express {express.numero} salvo no Drive")
            
        except Exception as e:
            results['express']['failed'] += 1
            import traceback
            print(f"❌ Erro ao fazer backup do relatório express {express.id} ({express.numero}): {str(e)}")
            print(f"   Traceback: {traceback.format_exc()}")
    
    return {
        'success': True,
        'message': f"Backup concluído! Relatórios: {results['relatorios']['success']}/{results['relatorios']['total']}, Express: {results['express']['success']}/{results['express']['total']}",
        'results': results
    }


def test_drive_connection() -> Dict[str, Any]:
    """
    Testar conexão com Google Drive (função de compatibilidade)
    
    Returns:
        Status da conexão
    """
    return drive_backup.test_connection()


def backup_to_drive(report_data: Dict[str, Any], project_name: str) -> Dict[str, Any]:
    """
    Função de compatibilidade para backup individual
    
    Args:
        report_data: Dados do relatório
        project_name: Nome do projeto
        
    Returns:
        Resultado do backup
    """
    return {
        'success': False,
        'message': 'Use a funcionalidade de Salvar Backup na área de administração'
    }
