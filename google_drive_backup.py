"""
Sistema de backup automático para Google Drive
Integração com pasta compartilhada para salvar relatórios e imagens
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any
import mimetypes
from urllib.parse import urlencode

class GoogleDriveBackup:
    """Sistema de backup para Google Drive usando API REST"""
    
    # ID da pasta compartilhada fornecida
    SHARED_FOLDER_ID = "1DasfSDL0832tx6AQcQGMFMlOm4JMboAx"
    
    # URLs da API do Google Drive
    DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
    UPLOAD_API_BASE = "https://www.googleapis.com/upload/drive/v3"
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Inicializar sistema de backup
        
        Args:
            access_token: Token de acesso OAuth 2.0 (se disponível)
        """
        self.access_token = access_token or os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN")
        
        # Fallback: Se não tiver token OAuth, tenta usar Service Account
        if not self.access_token:
            try:
                service_account_info = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
                if service_account_info:
                    import json
                    from google.oauth2 import service_account
                    from google.auth.transport.requests import Request
                    
                    creds_dict = json.loads(service_account_info)
                    credentials = service_account.Credentials.from_service_account_info(
                        creds_dict, scopes=['https://www.googleapis.com/auth/drive']
                    )
                    credentials.refresh(Request())
                    self.access_token = credentials.token
            except Exception as e:
                print(f"Erro ao usar Service Account: {e}")
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}" if self.access_token else None,
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Fazer requisição para API do Google Drive
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            url: URL da requisição
            **kwargs: Argumentos adicionais para requests
            
        Returns:
            Response object
        """
        if not self.access_token:
            raise Exception("Token de acesso não configurado")
            
        headers = kwargs.pop('headers', {})
        headers.update(self.headers)
        
        response = requests.request(method, url, headers=headers, **kwargs)
        
        if response.status_code == 401:
            raise Exception("Token de acesso expirado ou inválido")
        elif response.status_code >= 400:
            raise Exception(f"Erro na API do Google Drive: {response.status_code} - {response.text}")
            
        return response
    
    def create_project_folder(self, project_name: str) -> Optional[str]:
        """
        Criar pasta para o projeto dentro da pasta compartilhada
        
        Args:
            project_name: Nome do projeto
            
        Returns:
            ID da pasta criada ou None se houve erro
        """
        try:
            # Verificar se pasta já existe
            existing_folder = self.find_project_folder(project_name)
            if existing_folder:
                print(f"Pasta '{project_name}' já existe: {existing_folder}")
                return existing_folder
            
            # Criar nova pasta
            folder_metadata = {
                "name": project_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [self.SHARED_FOLDER_ID]
            }
            
            url = f"{self.DRIVE_API_BASE}/files"
            response = self._make_request("POST", url, json=folder_metadata)
            
            if response.status_code == 200:
                folder_data = response.json()
                folder_id = folder_data.get('id')
                print(f"Pasta '{project_name}' criada com sucesso: {folder_id}")
                return folder_id
            else:
                print(f"Erro ao criar pasta: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Erro ao criar pasta do projeto: {str(e)}")
            return None
    
    def find_project_folder(self, project_name: str) -> Optional[str]:
        """
        Encontrar pasta existente do projeto
        
        Args:
            project_name: Nome do projeto
            
        Returns:
            ID da pasta se encontrada, None caso contrário
        """
        try:
            # Buscar pasta dentro da pasta compartilhada
            query = f"name='{project_name}' and mimeType='application/vnd.google-apps.folder' and '{self.SHARED_FOLDER_ID}' in parents"
            params = {
                "q": query,
                "fields": "files(id, name)"
            }
            
            url = f"{self.DRIVE_API_BASE}/files"
            response = self._make_request("GET", url, params=params)
            
            if response.status_code == 200:
                files = response.json().get('files', [])
                if files:
                    folder_id = files[0]['id']
                    print(f"Pasta '{project_name}' encontrada: {folder_id}")
                    return folder_id
            
            return None
            
        except Exception as e:
            print(f"Erro ao buscar pasta do projeto: {str(e)}")
            return None
    
    def upload_file(self, file_path: str, project_name: str, file_name: Optional[str] = None) -> bool:
        """
        Fazer upload de arquivo para pasta do projeto
        
        Args:
            file_path: Caminho do arquivo local
            project_name: Nome do projeto
            file_name: Nome do arquivo no Drive (opcional, usa nome do arquivo se não especificado)
            
        Returns:
            True se upload foi bem sucedido, False caso contrário
        """
        try:
            # Verificar se arquivo existe
            if not os.path.exists(file_path):
                print(f"Arquivo não encontrado: {file_path}")
                return False
            
            # Obter ou criar pasta do projeto
            folder_id = self.find_project_folder(project_name)
            if not folder_id:
                folder_id = self.create_project_folder(project_name)
                if not folder_id:
                    print(f"Não foi possível criar/encontrar pasta para projeto: {project_name}")
                    return False
            
            # Preparar metadados do arquivo
            if not file_name:
                file_name = os.path.basename(file_path)
            
            # Detectar tipo MIME
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            file_metadata = {
                "name": file_name,
                "parents": [folder_id]
            }
            
            # Upload do arquivo usando multipart
            url = f"{self.UPLOAD_API_BASE}/files?uploadType=multipart"
            
            # Preparar dados multipart manualmente
            boundary = f"----formdata-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Parte 1: Metadados JSON
            metadata_part = f'--{boundary}\r\nContent-Type: application/json\r\n\r\n{json.dumps(file_metadata)}\r\n'
            
            # Parte 2: Conteúdo do arquivo
            file_part_header = f'--{boundary}\r\nContent-Type: {mime_type}\r\n\r\n'
            file_part_footer = f'\r\n--{boundary}--\r\n'
            
            # Ler arquivo
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Combinar todas as partes
            body = (metadata_part.encode('utf-8') + 
                   file_part_header.encode('utf-8') + 
                   file_content + 
                   file_part_footer.encode('utf-8'))
            
            # Headers para upload multipart
            upload_headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": f"multipart/related; boundary={boundary}",
                "Content-Length": str(len(body))
            }
            
            # Fazer upload
            response = requests.post(url, headers=upload_headers, data=body)
            
            if response.status_code == 200:
                file_data = response.json()
                file_id = file_data.get('id')
                print(f"Upload bem sucedido: {file_name} -> {file_id}")
                return True
            else:
                print(f"Erro no upload: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Erro no upload do arquivo: {str(e)}")
            return False
    
    def backup_report_files(self, report_data: Dict[str, Any], project_name: str) -> Dict[str, bool]:
        """
        Fazer backup de todos os arquivos relacionados a um relatório
        
        Args:
            report_data: Dados do relatório incluindo caminhos de arquivos
            project_name: Nome do projeto
            
        Returns:
            Dict com status do upload de cada arquivo
        """
        results = {}
        
        try:
            # Upload do PDF do relatório
            if 'pdf_path' in report_data and report_data['pdf_path']:
                pdf_name = f"relatorio_{report_data.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                results['pdf'] = self.upload_file(report_data['pdf_path'], project_name, pdf_name)
            
            # Upload de imagens anexadas
            if 'images' in report_data and report_data['images']:
                results['images'] = []
                for i, image_path in enumerate(report_data['images']):
                    if os.path.exists(image_path):
                        image_name = f"imagem_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                        upload_success = self.upload_file(image_path, project_name, image_name)
                        results['images'].append({
                            'path': image_path,
                            'success': upload_success
                        })
            
            return results
            
        except Exception as e:
            print(f"Erro no backup dos arquivos do relatório: {str(e)}")
            return {'error': str(e)}

def backup_to_drive(report_data: Dict[str, Any], project_name: str) -> Dict[str, Any]:
    """
    Função principal para backup automático no Google Drive
    
    Args:
        report_data: Dados do relatório
        project_name: Nome do projeto
        
    Returns:
        Resultado do backup com status de cada arquivo
    """
    try:
        # Verificar se token está disponível
        access_token = os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN")
        if not access_token:
            return {
                'success': False,
                'error': 'Token de acesso ao Google Drive não configurado',
                'message': 'Configure GOOGLE_DRIVE_ACCESS_TOKEN nas variáveis de ambiente'
            }
        
        # Inicializar sistema de backup
        backup_system = GoogleDriveBackup(access_token)
        
        # Fazer backup dos arquivos
        results = backup_system.backup_report_files(report_data, project_name)
        
        # Verificar se houve algum erro
        if 'error' in results:
            return {
                'success': False,
                'error': results['error'],
                'message': 'Erro durante o backup'
            }
        
        # Contar sucessos e falhas
        total_files = 0
        successful_uploads = 0
        
        if 'pdf' in results:
            total_files += 1
            if results['pdf']:
                successful_uploads += 1
        
        if 'images' in results:
            for img_result in results['images']:
                total_files += 1
                if img_result['success']:
                    successful_uploads += 1
        
        return {
            'success': successful_uploads > 0,
            'total_files': total_files,
            'successful_uploads': successful_uploads,
            'failed_uploads': total_files - successful_uploads,
            'results': results,
            'message': f'Backup concluído: {successful_uploads}/{total_files} arquivos enviados com sucesso'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Erro durante o backup para Google Drive'
        }

# Função de teste para verificar conectividade
def test_drive_connection() -> Dict[str, Any]:
    """
    Testar conexão com Google Drive
    
    Returns:
        Status da conexão
    """
    try:
        access_token = os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN")
        if not access_token:
            return {
                'success': False,
                'error': 'Token não configurado',
                'message': 'GOOGLE_DRIVE_ACCESS_TOKEN não encontrado'
            }
        
        backup_system = GoogleDriveBackup(access_token)
        
        # Testar acesso à pasta compartilhada
        url = f"{backup_system.DRIVE_API_BASE}/files/{backup_system.SHARED_FOLDER_ID}"
        response = backup_system._make_request("GET", url, params={"fields": "id,name,capabilities"})
        
        if response.status_code == 200:
            folder_data = response.json()
            return {
                'success': True,
                'folder_name': folder_data.get('name'),
                'folder_id': folder_data.get('id'),
                'message': 'Conexão com Google Drive estabelecida com sucesso'
            }
        else:
            return {
                'success': False,
                'error': f'Erro HTTP {response.status_code}',
                'message': 'Falha ao acessar pasta compartilhada'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Erro ao testar conexão com Google Drive'
        }