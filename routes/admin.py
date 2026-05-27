from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from database import get_db
from utils.helpers import admin_required, save_photo

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    db = get_db()
    busca = request.args.get('q', '').strip()
    if busca:
        users = db.execute(
            "SELECT * FROM users WHERE (nome LIKE ? OR email LIKE ?) AND id != ? ORDER BY nome",
            (f'%{busca}%', f'%{busca}%', session['user_id'])
        ).fetchall()
    else:
        users = db.execute(
            "SELECT * FROM users WHERE id != ? ORDER BY nome",
            (session['user_id'],)
        ).fetchall()

    total = db.execute("SELECT COUNT(*) as c FROM users").fetchone()['c']
    admins = db.execute("SELECT COUNT(*) as c FROM users WHERE role='admin'").fetchone()['c']
    return render_template('admin/dashboard.html', users=users, busca=busca,
                           total=total, admins=admins)


@admin_bp.route('/novo-usuario', methods=['GET', 'POST'])
@admin_required
def create_user():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        cpf = request.form.get('cpf', '').strip()
        telefone = request.form.get('telefone', '').strip()
        data_nasc = request.form.get('data_nasc', '').strip()
        role = request.form.get('role', 'user')
        senha = request.form.get('senha', '')
        foto_file = request.files.get('foto')

        erros = []
        if not nome:
            erros.append('Nome é obrigatório.')
        if not email or '@' not in email:
            erros.append('E-mail inválido.')
        if len(senha) < 8:
            erros.append('Senha deve ter no mínimo 8 caracteres.')

        db = get_db()
        if db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
            erros.append('E-mail já cadastrado.')

        if erros:
            for e in erros:
                flash(e, 'error')
            return render_template('admin/user_form.html', form=request.form, edit=False)

        foto_nome = save_photo(foto_file) if foto_file and foto_file.filename else None
        db.execute(
            '''INSERT INTO users (nome, email, cpf, telefone, data_nasc, senha_hash, foto, role)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (nome, email, cpf, telefone, data_nasc,
             generate_password_hash(senha), foto_nome, role)
        )
        db.commit()
        flash(f'Usuário {nome} criado com sucesso!', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/user_form.html', form={}, edit=False)


@admin_bp.route('/editar/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        cpf = request.form.get('cpf', '').strip()
        telefone = request.form.get('telefone', '').strip()
        data_nasc = request.form.get('data_nasc', '').strip()
        role = request.form.get('role', user['role'])
        foto_file = request.files.get('foto')

        erros = []
        if not nome:
            erros.append('Nome é obrigatório.')
        if not email or '@' not in email:
            erros.append('E-mail inválido.')
        dup = db.execute('SELECT id FROM users WHERE email=? AND id!=?', (email, user_id)).fetchone()
        if dup:
            erros.append('E-mail já em uso.')

        if erros:
            for e in erros:
                flash(e, 'error')
            return render_template('admin/user_form.html', form=request.form, user=user, edit=True)

        foto_nome = user['foto']
        if foto_file and foto_file.filename:
            nova = save_photo(foto_file)
            if nova:
                foto_nome = nova

        db.execute(
            'UPDATE users SET nome=?, email=?, cpf=?, telefone=?, data_nasc=?, foto=?, role=? WHERE id=?',
            (nome, email, cpf, telefone, data_nasc, foto_nome, role, user_id)
        )
        db.commit()
        flash(f'Usuário {nome} atualizado!', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/user_form.html', form=user, user=user, edit=True)


@admin_bp.route('/excluir/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == session['user_id']:
        flash('Você não pode excluir sua própria conta.', 'error')
        return redirect(url_for('admin.dashboard'))

    db = get_db()
    user = db.execute('SELECT nome FROM users WHERE id = ?', (user_id,)).fetchone()
    if user:
        db.execute('DELETE FROM users WHERE id = ?', (user_id,))
        db.commit()
        flash(f'Usuário "{user["nome"]}" excluído.', 'success')
    else:
        flash('Usuário não encontrado.', 'error')

    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/resetar-senha/<int:user_id>', methods=['POST'])
@admin_required
def reset_password(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('admin.dashboard'))

    nova_senha = 'Mudar@123'
    db.execute(
        'UPDATE users SET senha_hash=?, must_change_password=1 WHERE id=?',
        (generate_password_hash(nova_senha), user_id)
    )
    db.commit()
    flash(
        f'Senha de "{user["nome"]}" resetada para: <strong>{nova_senha}</strong>. '
        f'O usuário será solicitado a trocar no próximo login.',
        'success'
    )
    return redirect(url_for('admin.dashboard'))
