#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste direto da API do Cloudflare D1
"""

import requests
import json
from config import *

def test_d1_api_direct():
    """Testa diretamente a API do Cloudflare D1"""
    print("=== Teste Direto da API Cloudflare D1 ===")
    print(f"Account ID: {CLOUDFLARE_ACCOUNT_ID}")
    print(f"Database ID: {CLOUDFLARE_DATABASE_ID}")
    print(f"API Token: {CLOUDFLARE_API_TOKEN[:10]}...")
    print(f"API Base URL: {CLOUDFLARE_D1_API_BASE}")
    
    headers = {
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Teste 1: Listar turmas
    print("\n1. Testando listagem de turmas...")
    data = {
        'sql': 'SELECT * FROM turmas ORDER BY nome'
    }
    
    try:
        response = requests.post(
            f'{CLOUDFLARE_D1_API_BASE}/query',
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Sucesso! Resultado: {json.dumps(result, indent=2)}")
        else:
            print(f"   ✗ Erro: {response.text}")
            
    except Exception as e:
        print(f"   ✗ Exceção: {e}")
        import traceback
        traceback.print_exc()
    
    # Teste 2: Criar turma
    print("\n2. Testando criação de turma...")
    from datetime import datetime
    nome_turma_teste = f"API_Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    data = {
        'sql': 'INSERT INTO turmas (nome) VALUES (?)',
        'params': [nome_turma_teste]
    }
    
    try:
        response = requests.post(
            f'{CLOUDFLARE_D1_API_BASE}/query',
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Turma criada! Resultado: {json.dumps(result, indent=2)}")
        else:
            print(f"   ✗ Erro ao criar turma: {response.text}")
            
    except Exception as e:
        print(f"   ✗ Exceção ao criar turma: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_d1_api_direct()