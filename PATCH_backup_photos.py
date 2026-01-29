"""
PATCH para google_drive_backup.py

Este código substitui a lógica de leitura de fotos do filesystem
para ler do campo BYTEA do PostgreSQL (foto.imagem)

INSTRUÇÕES:
1. Substitua as linhas 595-648 do google_drive_backup.py com este código
2. Faça o mesmo para a seção de fotos Express (linhas ~680-720)
"""

# CÓDIGO CORRETO PARA BACKUP DE FOTOS:
# Substituir linhas 595-648

for foto in fotos:
    results['photos']['total'] += 1
    
    # PRIORIDADE 1: Ler foto do campo BYTEA do PostgreSQL (mesma lógica do PDF generator)
    photo_bytes = None
    photo_filename = None
    
    if hasattr(foto, 'imagem') and foto.imagem:
        # Foto armazenada no banco como BYTEA
        photo_bytes = bytes(foto.imagem)
        # Usar filename do banco ou gerar nome
        photo_filename = foto.filename or foto.filename_original or foto.filename_anotada or f"foto_{foto.id}.jpg"
    else:
        # Fallback: Tentar ler do disco (caso fotos antigas)
        local_filename = foto.filename or foto.filename_original or foto.filename_anotada
        
        if not local_filename:
            # Foto sem arquivo e sem imagem no banco
            results['photos']['failed'] += 1
            results['errors'].append(f"Foto {foto.id} sem dados (Rel {relatorio.numero})")
            continue
        
        file_path = os.path.join(upload_folder, local_filename)
        
        if not os.path.exists(file_path):
            # Tentar procurar apenas pelo basename
            file_path = os.path.join(upload_folder, os.path.basename(local_filename))
        
        if not os.path.exists(file_path):
            # Arquivo físico não encontrado e não tem no banco
            results['errors'].append(f"Arquivo não encontrado: {local_filename} (Rel {relatorio.numero})")
            results['photos']['failed'] += 1
            continue
        
        # Ler arquivo do disco
        try:
            with open(file_path, 'rb') as f:
                photo_bytes = f.read()
            photo_filename = local_filename
        except Exception as e:
            results['errors'].append(f"Erro lendo arquivo {local_filename}: {str(e)}")
            results['photos']['failed'] += 1
            continue
    
    # Nome para salvar no Drive
    # Formato: [ID]_[Categoria]_[Legenda].jpg
    categoria_clean = ''.join(c for c in (foto.tipo_servico or 'Geral') if c.isalnum())
    legenda_clean = ''.join(c for c in (foto.legenda or 'foto') if c.isalnum() or c in (' ', '-', '_'))[:30]
    ext = os.path.splitext(photo_filename)[1] or '.jpg'
    
    drive_filename = f"{foto.id}_{categoria_clean}_{legenda_clean}{ext}"
    
    # Verificar duplicidade
    if drive_filename in existing_files:
        results['photos']['skipped'] += 1
        continue
        
    # Upload usando bytes em memória
    try:
        file_size = len(photo_bytes)
        
        # Upload de bytes para o Drive (usar upload_pdf_bytes que aceita bytes)
        backup_instance.upload_pdf_bytes(photo_bytes, drive_filename, relatorio_folder_id)
        
        results['photos']['success'] += 1
        results['photos']['bytes'] += file_size
        print(f"✅ Foto {foto.id} enviada: {drive_filename} ({file_size} bytes)")
        
    except Exception as e:
        print(f"❌ Erro upload foto {foto.id}: {e}")
        results['photos']['failed'] += 1
        results['errors'].append(f"Erro upload foto {foto.id}: {str(e)}")
