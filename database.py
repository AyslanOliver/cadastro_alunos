import sqlite3
import requests
import json
from config import *

class DatabaseManager:
    def __init__(self):
        self.use_local = USE_LOCAL_DB
        if self.use_local:
            self.init_local_db()
    
    def init_local_db(self):
        """Inicializa o banco SQLite local e cria as tabelas"""
        conn = sqlite3.connect(LOCAL_DB_PATH)
        cursor = conn.cursor()
        
        # Criar tabela de turmas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS turmas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Criar tabela de alunos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alunos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                nascimento DATE NOT NULL,
                cpf TEXT UNIQUE NOT NULL,
                rg TEXT NOT NULL,
                celular TEXT NOT NULL,
                cep TEXT NOT NULL,
                graduacao TEXT NOT NULL,
                turma TEXT NOT NULL,
                foto TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (turma) REFERENCES turmas (nome)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query, params=None, fetch=False):
        """Executa uma query no banco de dados"""
        if self.use_local:
            return self._execute_local_query(query, params, fetch)
        else:
            return self._execute_d1_query(query, params, fetch)
    
    def _execute_local_query(self, query, params=None, fetch=False):
        """Executa query no SQLite local"""
        conn = sqlite3.connect(LOCAL_DB_PATH)
        conn.row_factory = sqlite3.Row  # Para retornar dicionários
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                if 'SELECT' in query.upper():
                    result = [dict(row) for row in cursor.fetchall()]
                else:
                    result = cursor.fetchall()
            else:
                result = cursor.rowcount
            
            conn.commit()
            return result
        finally:
            conn.close()
    
    def _execute_d1_query(self, query, params=None, fetch=False):
        """Executa query no Cloudflare D1"""
        headers = {
            'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'sql': query
        }
        
        if params:
            data['params'] = params
        
        response = requests.post(
            f'{CLOUDFLARE_D1_API_BASE}/query',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if fetch and 'result' in result:
                return result['result'][0]['results'] if result['result'] else []
            return result
        else:
            raise Exception(f'Erro na query D1: {response.text}')
    
    # Métodos específicos para turmas
    def criar_turma(self, nome_turma):
        """Cria uma nova turma"""
        query = "INSERT INTO turmas (nome) VALUES (?)"
        return self.execute_query(query, (nome_turma,))
    
    def listar_turmas(self):
        """Lista todas as turmas"""
        query = "SELECT * FROM turmas ORDER BY nome"
        return self.execute_query(query, fetch=True)
    
    def turma_existe(self, nome_turma):
        """Verifica se uma turma existe"""
        query = "SELECT COUNT(*) as count FROM turmas WHERE nome = ?"
        result = self.execute_query(query, (nome_turma,), fetch=True)
        return result[0]['count'] > 0 if result else False
    
    # Métodos específicos para alunos
    def criar_aluno(self, dados_aluno):
        """Cria um novo aluno"""
        query = '''
            INSERT INTO alunos (nome, nascimento, cpf, rg, celular, cep, graduacao, turma, foto)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            dados_aluno['nome'],
            dados_aluno['nascimento'],
            dados_aluno['cpf'],
            dados_aluno['rg'],
            dados_aluno['celular'],
            dados_aluno['cep'],
            dados_aluno['graduacao'],
            dados_aluno['turma'],
            dados_aluno.get('foto', '')
        )
        return self.execute_query(query, params)
    
    def listar_alunos_por_turma(self, nome_turma):
        """Lista todos os alunos de uma turma"""
        query = "SELECT * FROM alunos WHERE turma = ? ORDER BY nome"
        return self.execute_query(query, (nome_turma,), fetch=True)
    
    def buscar_aluno_por_cpf(self, cpf, turma=None):
        """Busca um aluno pelo CPF"""
        if turma:
            query = "SELECT * FROM alunos WHERE cpf = ? AND turma = ?"
            params = (cpf, turma)
        else:
            query = "SELECT * FROM alunos WHERE cpf = ?"
            params = (cpf,)
        
        result = self.execute_query(query, params, fetch=True)
        return result[0] if result else None
    
    def atualizar_aluno(self, cpf_original, turma, dados_aluno):
        """Atualiza os dados de um aluno"""
        query = '''
            UPDATE alunos 
            SET nome = ?, nascimento = ?, cpf = ?, rg = ?, celular = ?, cep = ?, graduacao = ?, foto = ?
            WHERE cpf = ? AND turma = ?
        '''
        params = (
            dados_aluno['nome'],
            dados_aluno['nascimento'],
            dados_aluno['cpf'],
            dados_aluno['rg'],
            dados_aluno['celular'],
            dados_aluno['cep'],
            dados_aluno['graduacao'],
            dados_aluno.get('foto', ''),
            cpf_original,
            turma
        )
        return self.execute_query(query, params)
    
    def deletar_aluno(self, cpf, turma):
        """Deleta um aluno"""
        query = "DELETE FROM alunos WHERE cpf = ? AND turma = ?"
        return self.execute_query(query, (cpf, turma))
    
    def contar_alunos_por_turma(self, nome_turma):
        """Conta o número de alunos em uma turma"""
        query = "SELECT COUNT(*) as count FROM alunos WHERE turma = ?"
        result = self.execute_query(query, (nome_turma,), fetch=True)
        return result[0]['count'] if result else 0
    
    def contar_total_turmas(self):
        """Conta o número total de turmas"""
        query = "SELECT COUNT(*) as count FROM turmas"
        result = self.execute_query(query, fetch=True)
        return result[0]['count'] if result else 0