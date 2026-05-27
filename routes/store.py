from flask import Blueprint, render_template, session

store_bp = Blueprint('store', __name__)


@store_bp.route('/loja')
def index():
    return render_template('store/index.html')


@store_bp.route('/produtos')
def produtos():
    return render_template('store/produtos.html')
