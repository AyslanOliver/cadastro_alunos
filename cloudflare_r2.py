import boto3
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from config import (
    CLOUDFLARE_R2_ACCESS_KEY_ID,
    CLOUDFLARE_R2_SECRET_ACCESS_KEY,
    CLOUDFLARE_R2_BUCKET_NAME,
    CLOUDFLARE_R2_ENDPOINT,
    CLOUDFLARE_R2_PUBLIC_URL,
    ALLOWED_EXTENSIONS
)

class CloudflareR2Manager:
    def __init__(self):
        """Inicializa o cliente S3 para Cloudflare R2"""
        # Configuração do cliente S3 para Cloudflare R2
        self.s3_client = boto3.client(
            's3',
            endpoint_url=CLOUDFLARE_R2_ENDPOINT,
            aws_access_key_id=CLOUDFLARE_R2_ACCESS_KEY_ID,
            aws_secret_access_key=CLOUDFLARE_R2_SECRET_ACCESS_KEY,
            region_name='auto'
        )
        self.bucket_name = CLOUDFLARE_R2_BUCKET_NAME
        self.public_url = CLOUDFLARE_R2_PUBLIC_URL
    
    def allowed_file(self, filename):
        """Verifica se o arquivo tem uma extensão permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    def generate_unique_filename(self, original_filename, turma_nome, aluno_nome):
        """Gera um nome único para o arquivo"""
        if not original_filename:
            return None
        
        # Limpar nomes para usar no caminho
        turma_clean = secure_filename(turma_nome)
        aluno_clean = secure_filename(aluno_nome)
        
        # Obter extensão do arquivo
        file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
        
        # Gerar nome único com timestamp e UUID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        # Estrutura: turma/aluno_timestamp_uuid.ext
        filename = f"{turma_clean}/{aluno_clean}_{timestamp}_{unique_id}.{file_ext}"
        
        return filename
    
    def upload_file(self, file_obj, turma_nome, aluno_nome, original_filename):
        """Faz upload de um arquivo para o Cloudflare R2"""
        try:
            # Verificar se o arquivo é permitido
            if not self.allowed_file(original_filename):
                raise ValueError(f"Tipo de arquivo não permitido. Extensões permitidas: {', '.join(ALLOWED_EXTENSIONS)}")
            
            # Gerar nome único para o arquivo
            unique_filename = self.generate_unique_filename(original_filename, turma_nome, aluno_nome)
            
            if not unique_filename:
                raise ValueError("Nome de arquivo inválido")
            
            # Fazer upload para R2
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                unique_filename,
                ExtraArgs={
                    'ContentType': self._get_content_type(original_filename),
                    'Metadata': {
                        'turma': turma_nome,
                        'aluno': aluno_nome,
                        'upload_date': datetime.now().isoformat()
                    }
                }
            )
            
            # Retornar URL pública do arquivo
            public_url = f"{self.public_url}/{unique_filename}"
            
            return {
                'success': True,
                'url': public_url,
                'filename': unique_filename,
                'message': 'Upload realizado com sucesso'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Erro no upload: {str(e)}'
            }
    
    def delete_file(self, filename):
        """Deleta um arquivo do Cloudflare R2"""
        try:
            if not filename:
                return {'success': True, 'message': 'Nenhum arquivo para deletar'}
            
            # Extrair apenas o nome do arquivo da URL se necessário
            if filename.startswith('http'):
                filename = filename.replace(f"{self.public_url}/", "")
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=filename
            )
            
            return {
                'success': True,
                'message': 'Arquivo deletado com sucesso'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Erro ao deletar arquivo: {str(e)}'
            }
    
    def _get_content_type(self, filename):
        """Determina o Content-Type baseado na extensão do arquivo"""
        if not filename or '.' not in filename:
            return 'application/octet-stream'
        
        ext = filename.rsplit('.', 1)[1].lower()
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        
        return content_types.get(ext, 'application/octet-stream')
    
    def list_files(self, prefix=''):
        """Lista arquivos no bucket (útil para debug)"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'url': f"{self.public_url}/{obj['Key']}"
                    })
            
            return {
                'success': True,
                'files': files
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Instância global do gerenciador R2
r2_manager = CloudflareR2Manager()