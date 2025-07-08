#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar a integração com Cloudflare R2
"""

import os
import sys
from io import BytesIO
from cloudflare_r2 import r2_manager

def test_r2_connection():
    """Testa a conexão com o Cloudflare R2"""
    print("🔍 Testando conexão com Cloudflare R2...")
    
    try:
        # Tentar listar arquivos no bucket
        result = r2_manager.list_files()
        
        if result['success']:
            print("✅ Conexão com R2 estabelecida com sucesso!")
            print(f"📁 Bucket: {r2_manager.bucket_name}")
            print(f"🔗 URL público: {r2_manager.public_url}")
            
            files = result.get('files', [])
            if files:
                print(f"📄 Arquivos encontrados: {len(files)}")
                for file in files[:5]:  # Mostrar apenas os primeiros 5
                    print(f"   - {file['key']} ({file['size']} bytes)")
            else:
                print("📄 Nenhum arquivo encontrado no bucket (isso é normal para um bucket novo)")
            
            return True
        else:
            print(f"❌ Erro na conexão: {result.get('error', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na conexão com R2: {str(e)}")
        return False

def test_upload():
    """Testa o upload de um arquivo de teste"""
    print("\n📤 Testando upload de arquivo...")
    
    try:
        # Criar um arquivo de teste em memória
        test_content = b"Este e um arquivo de teste para o Cloudflare R2"
        test_file = BytesIO(test_content)
        
        # Fazer upload
        result = r2_manager.upload_file(
            test_file,
            "turma_teste",
            "aluno_teste",
            "teste.txt"
        )
        
        if result['success']:
            print("✅ Upload realizado com sucesso!")
            print(f"🔗 URL: {result['url']}")
            print(f"📁 Arquivo: {result['filename']}")
            
            # Tentar deletar o arquivo de teste
            print("\n🗑️ Deletando arquivo de teste...")
            delete_result = r2_manager.delete_file(result['filename'])
            
            if delete_result['success']:
                print("✅ Arquivo de teste deletado com sucesso!")
            else:
                print(f"⚠️ Aviso: Não foi possível deletar o arquivo de teste: {delete_result['message']}")
            
            return True
        else:
            print(f"❌ Erro no upload: {result.get('message', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de upload: {str(e)}")
        return False

def main():
    """Função principal"""
    print("🚀 Iniciando testes do Cloudflare R2...\n")
    
    # Verificar se as configurações estão presentes
    from config import CLOUDFLARE_R2_BUCKET_NAME, CLOUDFLARE_R2_ENDPOINT, CLOUDFLARE_API_TOKEN
    
    print(f"⚙️ Configurações:")
    print(f"   Bucket: {CLOUDFLARE_R2_BUCKET_NAME}")
    print(f"   Endpoint: {CLOUDFLARE_R2_ENDPOINT}")
    print(f"   Token: {'*' * (len(CLOUDFLARE_API_TOKEN) - 4) + CLOUDFLARE_API_TOKEN[-4:]}")
    print()
    
    # Teste 1: Conexão
    connection_ok = test_r2_connection()
    
    if connection_ok:
        # Teste 2: Upload
        upload_ok = test_upload()
        
        if upload_ok:
            print("\n🎉 Todos os testes passaram! O Cloudflare R2 está configurado corretamente.")
            print("\n📝 Próximos passos:")
            print("   1. Certifique-se de que o bucket está configurado como público (se necessário)")
            print("   2. Configure um domínio personalizado para o R2 (opcional)")
            print("   3. A aplicação está pronta para usar o Cloudflare R2!")
        else:
            print("\n⚠️ A conexão funciona, mas há problemas com upload. Verifique as permissões.")
    else:
        print("\n❌ Problemas na conexão. Verifique:")
        print("   1. Se o bucket existe no Cloudflare R2")
        print("   2. Se as credenciais estão corretas")
        print("   3. Se o token tem permissões para R2")
        print("\n💡 Dica: Você pode precisar criar credenciais R2 específicas no painel do Cloudflare.")

if __name__ == "__main__":
    main()