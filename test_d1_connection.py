#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar a conexão com Cloudflare D1 e operações de turma
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from datetime import datetime

def test_d1_connection():
    """Testa a conexão e operações básicas com Cloudflare D1"""
    print("=== Teste de Conexão Cloudflare D1 ===")
    
    try:
        # Inicializar o DatabaseManager
        db_manager = DatabaseManager()
        print(f"✓ DatabaseManager inicializado (usando Cloudflare D1: {not db_manager.use_local})")
        
        # Testar listagem de turmas existentes
        print("\n1. Listando turmas existentes...")
        turmas = db_manager.listar_turmas()
        print(f"   Turmas encontradas: {len(turmas)}")
        for turma in turmas:
            print(f"   - {turma['nome']}")
        
        # Testar criação de uma nova turma de teste
        nome_turma_teste = f"Teste_Conexao_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"\n2. Criando turma de teste: {nome_turma_teste}")
        
        try:
            print("   Executando query de criação...")
            resultado = db_manager.criar_turma(nome_turma_teste)
            print(f"   ✓ Turma criada com sucesso! Resultado: {resultado}")
            
            # Verificar se a turma foi realmente criada
            print("   Verificando se turma existe...")
            if db_manager.turma_existe(nome_turma_teste):
                print(f"   ✓ Turma {nome_turma_teste} confirmada no banco")
            else:
                print(f"   ✗ Turma {nome_turma_teste} NÃO foi encontrada no banco")
                
        except Exception as e:
            print(f"   ✗ Erro ao criar turma: {e}")
            import traceback
            traceback.print_exc()
        
        # Listar turmas novamente
        print("\n3. Listando turmas após criação...")
        turmas_apos = db_manager.listar_turmas()
        print(f"   Total de turmas: {len(turmas_apos)}")
        for turma in turmas_apos:
            print(f"   - {turma['nome']}")
        
        print("\n=== Teste Concluído ===")
        
    except Exception as e:
        print(f"✗ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_d1_connection()