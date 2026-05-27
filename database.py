import sqlite3
import click
from flask import g, current_app
from werkzeug.security import generate_password_hash


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db(app):
    app.teardown_appcontext(close_db)

    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                cpf TEXT,
                telefone TEXT,
                data_nasc TEXT,
                senha_hash TEXT NOT NULL,
                foto TEXT DEFAULT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                must_change_password INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Criar admin padrão se não existir
        existing = db.execute("SELECT id FROM users WHERE email = 'admin@deathnote.com'").fetchone()
        if not existing:
            db.execute(
                '''INSERT INTO users (nome, email, senha_hash, role, cpf, telefone, data_nasc)
                   VALUES (?, ?, ?, 'admin', '', '', '')''',
                ('Administrador', 'admin@deathnote.com', generate_password_hash('Admin@123'))
            )
            db.commit()

    @app.cli.command('init-db')
    def init_db_command():
        """Reinicia o banco de dados."""
        click.echo('Banco inicializado.')
