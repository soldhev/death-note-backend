from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
from utils.helpers import save_photo
import secrets

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    return redirect(url_for('store.index'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user and check_password_hash(user['senha_hash'], senha):
            session.clear()
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['nome'] = user['nome']
            session['foto'] = user['foto']

            if user['must_change_password']:
                flash('Por segurança, você precisa alterar sua senha.', 'warning')
                return redirect(url_for('user.change_password'))

            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('user.dashboard'))
        else:
            flash('E-mail ou senha inválidos.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        cpf = request.form.get('cpf', '').strip()
        telefone = request.form.get('telefone', '').strip()
        data_nasc = request.form.get('data_nasc', '').strip()
        senha = request.form.get('senha', '')
        conf_senha = request.form.get('conf_senha', '')
        foto_file = request.files.get('foto')

        # Validações
        erros = []
        if not nome or len(nome.split()) < 2:
            erros.append('Informe nome e sobrenome.')
        if not email or '@' not in email:
            erros.append('E-mail inválido.')
        if not senha or len(senha) < 8:
            erros.append('Senha deve ter no mínimo 8 caracteres.')
        if senha != conf_senha:
            erros.append('As senhas não coincidem.')

        db = get_db()
        if db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
            erros.append('E-mail já cadastrado.')

        if erros:
            for e in erros:
                flash(e, 'error')
            return render_template('auth/register.html', form=request.form)

        foto_nome = save_photo(foto_file) if foto_file and foto_file.filename else None
        senha_hash = generate_password_hash(senha)

        db.execute(
            '''INSERT INTO users (nome, email, cpf, telefone, data_nasc, senha_hash, foto, role)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'user')''',
            (nome, email, cpf, telefone, data_nasc, senha_hash, foto_nome)
        )
        db.commit()

        flash('Conta criada com sucesso! Faça seu login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form={})


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/esqueci-senha', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        # Sempre mostrar msg genérica por segurança
        flash('Se este e-mail estiver cadastrado, um link de recuperação foi enviado.', 'info')
        # Aqui você integraria com e-mail; para demo, mostramos token na tela
        if user:
            token = secrets.token_urlsafe(24)
            # Salvar token temporário no banco (simplificado: reusar must_change_password)
            db.execute('UPDATE users SET must_change_password = 1 WHERE id = ?', (user['id'],))
            db.commit()
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')
