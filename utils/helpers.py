import os
import uuid
from functools import wraps
from flask import session, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_photo(file):
    """Salva foto e retorna o nome do arquivo salvo."""
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        return filename
    return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Faça login para continuar.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Faça login para continuar.', 'error')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash('Acesso restrito a administradores.', 'error')
            return redirect(url_for('user.dashboard'))
        return f(*args, **kwargs)
    return decorated
