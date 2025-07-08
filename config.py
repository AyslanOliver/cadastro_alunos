import os
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# Configurações do Cloudflare D1
CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID', 'c0c527df17c1d65d2ca35df56b1f0a71')
CLOUDFLARE_DATABASE_ID = os.getenv('CLOUDFLARE_DATABASE_ID', '9a3795aa-7ddb-4245-b58d-2d150595d4e1')
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN', 'a9fb469af686c77579660fac76b5739367523')

# URL base da API do Cloudflare D1
CLOUDFLARE_D1_API_BASE = f'https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/d1/database/{CLOUDFLARE_DATABASE_ID}'

# Configurações do Cloudflare R2
CLOUDFLARE_R2_ACCESS_KEY_ID = os.getenv('CLOUDFLARE_R2_ACCESS_KEY_ID')
CLOUDFLARE_R2_SECRET_ACCESS_KEY = os.getenv('CLOUDFLARE_R2_SECRET_ACCESS_KEY')
CLOUDFLARE_R2_BUCKET_NAME = os.getenv('CLOUDFLARE_R2_BUCKET_NAME', 'cadastro-alunos-fotos')
CLOUDFLARE_R2_ENDPOINT = os.getenv('CLOUDFLARE_R2_ENDPOINT', 'https://your-account-id.r2.cloudflarestorage.com')
CLOUDFLARE_R2_PUBLIC_URL = os.getenv('CLOUDFLARE_R2_PUBLIC_URL', 'https://pub-your-bucket-id.r2.dev')

# Configurações do Flask
SECRET_KEY = os.getenv('SECRET_KEY', 'sua-chave-secreta-aqui')
UPLOAD_FOLDER = 'static/uploads'

# Configurações de desenvolvimento (usar SQLite local)
USE_LOCAL_DB = os.getenv('USE_LOCAL_DB', 'True').lower() == 'true'
LOCAL_DB_PATH = 'cadastro_alunos.db'

# Configurações de upload
USE_CLOUDFLARE_R2 = os.getenv('USE_CLOUDFLARE_R2', 'True').lower() == 'true'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}