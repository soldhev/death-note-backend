from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
from utils.helpers import login_required, save_photo
import os

user_bp = Blueprint('user', __name__, url_prefix='/usuario')


@user_bp.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return render_template('user/dashboard.html', user=user)


@user_bp.route('/editar', methods=['GET', 'POST'])
@login_required
def edit_profile():
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        cpf = request.form.get('cpf', '').strip()
        telefone = request.form.get('telefone', '').strip()
        data_nasc = request.form.get('data_nasc', '').strip()
        foto_file = request.files.get('foto')

        erros = []
        if not nome or len(nome.split()) < 2:
            erros.append('Informe nome e sobrenome.')
        if not email or '@' not in email:
            erros.append('E-mail inválido.')

        # Checar email duplicado (exceto o próprio)
        dup = db.execute('SELECT id FROM users WHERE email = ? AND id != ?',
                         (email, session['user_id'])).fetchone()
        if dup:
            erros.append('E-mail já em uso por outro usuário.')

        if erros:
            for e in erros:
                flash(e, 'error')
            return render_template('user/edit_profile.html', user=user)

        foto_nome = user['foto']
        if foto_file and foto_file.filename:
            nova_foto = save_photo(foto_file)
            if nova_foto:
                foto_nome = nova_foto

        db.execute(
            'UPDATE users SET nome=?, email=?, cpf=?, telefone=?, data_nasc=?, foto=? WHERE id=?',
            (nome, email, cpf, telefone, data_nasc, foto_nome, session['user_id'])
        )
        db.commit()

        session['nome'] = nome
        session['foto'] = foto_nome
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('user.dashboard'))

    return render_template('user/edit_profile.html', user=user)


@user_bp.route('/alterar-senha', methods=['GET', 'POST'])
@login_required
def change_password():
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual', '')
        nova_senha = request.form.get('nova_senha', '')
        conf_senha = request.form.get('conf_senha', '')

        erros = []

        # Se não precisa mudar senha obrigatoriamente, valida senha atual
        if not user['must_change_password']:
            if not check_password_hash(user['senha_hash'], senha_atual):
                erros.append('Senha atual incorreta.')

        if len(nova_senha) < 8:
            erros.append('Nova senha deve ter no mínimo 8 caracteres.')
        if nova_senha != conf_senha:
            erros.append('As senhas não coincidem.')

        if erros:
            for e in erros:
                flash(e, 'error')
            return render_template('user/change_password.html', user=user)

        db.execute(
            'UPDATE users SET senha_hash=?, must_change_password=0 WHERE id=?',
            (generate_password_hash(nova_senha), session['user_id'])
        )
        db.commit()
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('user.dashboard'))

    return render_template('user/change_password.html', user=user)
