from flask import Flask, render_template, request, redirect, url_for, session, send_file, make_response, flash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import pandas as pd
import os
import re
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = 'chave_super_secreta'

# Funções de validação
def validar_cpf(cpf):
    """Valida CPF brasileiro"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = 11 - (soma % 11)
    if digito1 >= 10:
        digito1 = 0
    
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = 11 - (soma % 11)
    if digito2 >= 10:
        digito2 = 0
    
    return cpf[-2:] == f'{digito1}{digito2}'

def validar_celular(celular):
    """Valida formato de celular brasileiro"""
    padrao = r'^\(\d{2}\)\s\d{4,5}-\d{4}$'
    return bool(re.match(padrao, celular))

def validar_cep(cep):
    """Valida formato de CEP brasileiro"""
    padrao = r'^\d{5}-\d{3}$'
    return bool(re.match(padrao, cep))

def validar_nome(nome):
    """Valida nome (apenas letras e espaços)"""
    padrao = r'^[A-Za-zÀ-ÿ\s]{3,100}$'
    return bool(re.match(padrao, nome.strip()))

def validar_dados_aluno(dados):
    """Valida todos os dados do aluno"""
    erros = []
    
    if not validar_nome(dados.get('nome', '')):
        erros.append('Nome deve conter apenas letras e espaços (3-100 caracteres)')
    
    if not validar_cpf(dados.get('cpf', '')):
        erros.append('CPF inválido')
    
    if not validar_celular(dados.get('celular', '')):
        erros.append('Celular deve estar no formato (00) 00000-0000')
    
    if not validar_cep(dados.get('cep', '')):
        erros.append('CEP deve estar no formato 00000-000')
    
    if not dados.get('nascimento'):
        erros.append('Data de nascimento é obrigatória')
    
    if not dados.get('rg', '').strip():
        erros.append('RG é obrigatório')
    
    if not dados.get('graduacao', '').strip():
        erros.append('Graduação é obrigatória')
    
    return erros

client = MongoClient('mongodb+srv://ayslano37:Walkingtonn1@demolicao.fk6aapp.mongodb.net/')
db = client['cadastro_alunos']

# Redirecionar para login
@app.route('/')
def index():
    return redirect(url_for('login'))



# Formulário de cadastro específico para uma turma
@app.route('/cadastro/<nome_turma>', methods=['GET', 'POST'])
def cadastro_turma(nome_turma):
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    # Verificar se a turma existe
    turma_existe = db.turmas.find_one({'nome': nome_turma})
    if not turma_existe:
        return "Turma não encontrada.", 404
    
    if request.method == 'POST':
        dados = {
            'nome': request.form['nome'].strip(),
            'nascimento': request.form['nascimento'],
            'cpf': request.form['cpf'],
            'rg': request.form['rg'].strip(),
            'celular': request.form['celular'],
            'cep': request.form['cep'],
            'graduacao': request.form['graduacao'].strip()
        }
        
        # Validar dados
        erros = validar_dados_aluno(dados)
        
        # Verificar se CPF já existe
        cpf_existente = db.alunos.find_one({'cpf': dados['cpf']})
        if cpf_existente:
            erros.append('CPF já cadastrado no sistema')
        
        if erros:
            for erro in erros:
                flash(erro, 'error')
            return render_template('cadastro_turma_especifico.html', turma=nome_turma, dados=dados)

        pasta_turma = os.path.join(app.config['UPLOAD_FOLDER'], nome_turma)
        os.makedirs(pasta_turma, exist_ok=True)

        foto = request.files['foto']
        if foto.filename != '':
            filename = secure_filename(foto.filename)
            caminho_foto = os.path.join(pasta_turma, filename)
            foto.save(caminho_foto)
        else:
            caminho_foto = ''

        db.alunos.insert_one({
            'nome': dados['nome'],
            'nascimento': dados['nascimento'],
            'cpf': dados['cpf'],
            'rg': dados['rg'],
            'celular': dados['celular'],
            'cep': dados['cep'],
            'graduacao': dados['graduacao'],
            'turma': nome_turma,
            'foto': caminho_foto
        })
        
        flash('Aluno cadastrado com sucesso!', 'success')
        return redirect(url_for('painel_turma', nome_turma=nome_turma))

    return render_template('cadastro_turma_especifico.html', turma=nome_turma)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        if usuario == 'admin' and senha == '1234':
            session['logado'] = True
            return redirect(url_for('painel'))
        else:
            return 'Login inválido!'
    return render_template('login.html')

# Painel principal = lista de turmas
@app.route('/painel')
def painel():
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    turmas = list(db.turmas.find())
    
    # Adicionar contagem de alunos para cada turma
    turmas_com_contagem = []
    for turma in turmas:
        contagem_alunos = db.alunos.count_documents({'turma': turma['nome']})
        turma['contagem_alunos'] = contagem_alunos
        turmas_com_contagem.append(turma)
    
    # Contagem total de turmas
    total_turmas = len(turmas)
    
    return render_template('painel.html', turmas=turmas_com_contagem, total_turmas=total_turmas)

# Visualizar alunos de uma turma
@app.route('/painel/turma/<nome_turma>')
def painel_turma(nome_turma):
    if not session.get('logado'):
        return redirect(url_for('login'))
    alunos = list(db.alunos.find({'turma': nome_turma}))
    return render_template('painel_turma.html', turma=nome_turma, alunos=alunos)

# Cadastro de nova turma
@app.route('/cadastrar_turma', methods=['GET', 'POST'])
def cadastrar_turma():
    if not session.get('logado'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        nome_turma = request.form['nome_turma']
        db.turmas.insert_one({'nome': nome_turma})
        return redirect(url_for('painel'))
    return render_template('cadastrar_turma.html')

# Exportar turma para Excel
@app.route('/exportar_excel/<nome_turma>')
def exportar_excel(nome_turma):
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    # Buscar alunos da turma
    alunos = list(db.alunos.find({'turma': nome_turma}))
    
    if not alunos:
        return "Nenhum aluno encontrado nesta turma.", 404
    
    # Preparar dados para o DataFrame
    dados_excel = []
    for aluno in alunos:
        dados_excel.append({
            'Nome': aluno.get('nome', ''),
            'Data de Nascimento': aluno.get('nascimento', ''),
            'CPF': aluno.get('cpf', ''),
            'RG': aluno.get('rg', ''),
            'Celular': aluno.get('celular', ''),
            'CEP': aluno.get('cep', ''),
            'Graduação': aluno.get('graduacao', ''),
            'Turma': aluno.get('turma', ''),
            'Foto': 'Sim' if aluno.get('foto') else 'Não'
        })
    
    # Criar DataFrame
    df = pd.DataFrame(dados_excel)
    
    # Criar arquivo Excel em memória
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'Turma_{nome_turma}', index=False)
        
        # Ajustar largura das colunas
        worksheet = writer.sheets[f'Turma_{nome_turma}']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    
    # Preparar resposta
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'Turma_{nome_turma}_{timestamp}.xlsx'
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

# Deletar aluno
@app.route('/deletar_aluno/<nome_turma>/<cpf>')
def deletar_aluno(nome_turma, cpf):
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    # Buscar o aluno para obter o caminho da foto
    aluno = db.alunos.find_one({'cpf': cpf, 'turma': nome_turma})
    
    if aluno:
        # Deletar foto se existir
        if aluno.get('foto') and os.path.exists(aluno['foto']):
            try:
                os.remove(aluno['foto'])
            except:
                pass  # Ignorar erro se não conseguir deletar a foto
        
        # Deletar aluno do banco
        db.alunos.delete_one({'cpf': cpf, 'turma': nome_turma})
    
    return redirect(url_for('painel_turma', nome_turma=nome_turma))

# Editar aluno
@app.route('/editar_aluno/<nome_turma>/<cpf>', methods=['GET', 'POST'])
def editar_aluno(nome_turma, cpf):
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    aluno = db.alunos.find_one({'cpf': cpf, 'turma': nome_turma})
    if not aluno:
        return "Aluno não encontrado.", 404
    
    if request.method == 'POST':
        dados = {
            'nome': request.form['nome'].strip(),
            'nascimento': request.form['nascimento'],
            'cpf': request.form['cpf'],
            'rg': request.form['rg'].strip(),
            'celular': request.form['celular'],
            'cep': request.form['cep'],
            'graduacao': request.form['graduacao'].strip()
        }
        
        # Validar dados
        erros = validar_dados_aluno(dados)
        
        # Verificar se CPF já existe (exceto o próprio aluno)
        if dados['cpf'] != cpf:  # Se mudou o CPF
            cpf_existente = db.alunos.find_one({'cpf': dados['cpf']})
            if cpf_existente:
                erros.append('CPF já cadastrado no sistema')
        
        if erros:
            for erro in erros:
                flash(erro, 'error')
            return render_template('editar_aluno.html', aluno=aluno, turma=nome_turma)

        pasta_turma = os.path.join(app.config['UPLOAD_FOLDER'], nome_turma)
        os.makedirs(pasta_turma, exist_ok=True)

        foto = request.files['foto']
        caminho_foto = aluno.get('foto', '')  # Manter foto atual se não enviar nova
        
        if foto.filename != '':
            # Deletar foto antiga se existir
            if caminho_foto and os.path.exists(caminho_foto):
                try:
                    os.remove(caminho_foto)
                except:
                    pass
            
            # Salvar nova foto
            filename = secure_filename(foto.filename)
            caminho_foto = os.path.join(pasta_turma, filename)
            foto.save(caminho_foto)

        # Atualizar dados do aluno
        db.alunos.update_one(
            {'cpf': cpf, 'turma': nome_turma},
            {'$set': {
                'nome': dados['nome'],
                'nascimento': dados['nascimento'],
                'cpf': dados['cpf'],
                'rg': dados['rg'],
                'celular': dados['celular'],
                'cep': dados['cep'],
                'graduacao': dados['graduacao'],
                'foto': caminho_foto
            }}
        )
        
        flash('Aluno atualizado com sucesso!', 'success')
        return redirect(url_for('painel_turma', nome_turma=nome_turma))

    return render_template('editar_aluno.html', aluno=aluno, turma=nome_turma)

@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
