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
