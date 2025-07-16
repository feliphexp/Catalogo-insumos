import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect
from fpdf import FPDF
from datetime import datetime
import urllib.parse
# Nenhuma importação de PIX ou CRC necessária aqui, a função é autocontida

# --- Configuração da Aplicação ---
app = Flask(__name__)
DB_NAME = 'database.db'
app.config['SECRET_KEY'] = 'a-chave-que-vai-funcionar-agora-100-porcento-final'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Inicialização dos Módulos Flask ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELOS ---
class Product(db.Model):
    __tablename__ = 'produto'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- ROTAS ---
@app.route('/')
@login_required
def catalogo():
    products = Product.query.all()
    search_query = request.args.get('q', '')
    if search_query:
        search_term = f"%{search_query}%"
        products = Product.query.filter(Product.nome.ilike(search_term)).all()
    return render_template('catalogo.html', products=products, search_query=search_query)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            session.pop('cart', None) 
            return redirect(url_for('catalogo'))
        else:
            flash('Usuário ou senha inválidos.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('cart', None)
    logout_user()
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'admin': abort(403)
    if request.method == 'POST':
        new_product = Product(nome=request.form['nome'], preco=float(request.form['preco']))
        db.session.add(new_product)
        db.session.commit()
        flash('Produto adicionado com sucesso!')
        return redirect(url_for('catalogo'))
    return render_template('editar_produto.html', action='add')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    if current_user.role != 'admin': abort(403)
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.nome = request.form['nome']
        product.preco = float(request.form['preco'])
        db.session.commit()
        flash('Produto atualizado com sucesso!')
        return redirect(url_for('catalogo'))
    return render_template('editar_produto.html', product=product, action='edit')

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    if current_user.role != 'admin': abort(403)
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Produto excluído com sucesso!')
    return redirect(url_for('catalogo'))

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin': abort(403)
    users = User.query.order_by(User.username).all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/add', methods=['POST'])
@login_required
def add_new_user():
    if current_user.role != 'admin': abort(403)
    username, password, role = request.form.get('username'), request.form.get('password'), request.form.get('role')
    if not all([username, password, role]):
        flash("Todos os campos são obrigatórios.")
        return redirect(url_for('admin_users'))
    if User.query.filter_by(username=username).first():
        flash("Este nome de usuário já existe.")
        return redirect(url_for('admin_users'))
    new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'), role=role)
    db.session.add(new_user)
    db.session.commit()
    flash(f"Usuário '{username}' criado com sucesso!")
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    if current_user.role != 'admin': abort(403)
    user_to_delete = User.query.get_or_404(id)
    if user_to_delete.id == current_user.id:
        flash("Você não pode deletar a si mesmo.")
        return redirect(url_for('admin_users'))
    db.session.delete(user_to_delete)
    db.session.commit()
    flash("Usuário deletado com sucesso.")
    return redirect(url_for('admin_users'))

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    session.setdefault('cart', {})
    quantity = request.form.get('quantity', 1, type=int)
    product_id_str = str(product_id)
    session['cart'][product_id_str] = session['cart'].get(product_id_str, 0) + quantity
    session.modified = True
    flash(f'{quantity}x produto(s) adicionado(s) ao carrinho!')
    return redirect(url_for('catalogo'))

@app.route('/cart')
@login_required
def cart():
    cart_items, total_price = [], 0
    if 'cart' in session:
        for product_id, quantity in session['cart'].items():
            product = db.session.get(Product, int(product_id))
            if product:
                item_total = product.preco * quantity
                cart_items.append({'product': product, 'quantity': quantity, 'total': item_total})
                total_price += item_total
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    product_id_str = str(product_id)
    if 'cart' in session and product_id_str in session['cart']:
        session['cart'].pop(product_id_str)
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/clear_cart')
@login_required
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('cart'))

@app.route('/generate_pdf', methods=['POST'])
@login_required
def generate_pdf():
    customer_name = request.form.get('customer_name')
    if not customer_name:
        flash("Por favor, informe o nome do cliente.")
        return redirect(url_for('cart'))
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(40, 10, f'Pedido de {customer_name}')
    session.pop('cart', None)
    response = make_response(pdf.output(dest='S'))
    response.headers.set('Content-Disposition', 'attachment', filename=f'pedido_{customer_name}.pdf')
    response.headers.set('Content-Type', 'application/pdf')
    return response

# --- FUNÇÃO PARA GERAR O PIX COPIA E COLA ---
def generate_pix_br_code(pix_key, merchant_name, merchant_city, amount, txid="***"):
    def format_field(id, value):
        return f"{id:02d}{len(value):02d}{value}"

    merchant_name = ''.join(e for e in merchant_name if e.isalnum() or e.isspace())[:25]
    merchant_city = ''.join(e for e in merchant_city if e.isalnum() or e.isspace())[:15]

    payload_format_indicator = format_field(0, "01")
    merchant_account_info = format_field(26, format_field(0, "br.gov.bcb.pix") + format_field(1, pix_key))
    merchant_category_code = format_field(52, "0000")
    transaction_currency = format_field(53, "986")
    transaction_amount = format_field(54, f"{amount:.2f}")
    country_code = format_field(58, "BR")
    merchant_name_field = format_field(59, merchant_name)
    merchant_city_field = format_field(60, merchant_city)
    additional_data_field = format_field(62, format_field(5, txid))
    
    payload_to_crc = (
        payload_format_indicator + merchant_account_info + merchant_category_code +
        transaction_currency + transaction_amount + country_code +
        merchant_name_field + merchant_city_field + additional_data_field + "6304"
    )
    
    polynom = 0x1021
    crc = 0xFFFF
    for byte in payload_to_crc.encode('utf-8'):
        crc ^= (byte << 8)
        for _ in range(8):
            if (crc & 0x8000):
                crc = (crc << 1) ^ polynom
            else:
                crc <<= 1
    checksum = crc & 0xFFFF

    return payload_to_crc + f"{checksum:04X}"


@app.route('/share_on_whatsapp', methods=['POST'])
@login_required
def share_on_whatsapp():
    customer_name = request.form.get('whatsapp_customer_name')
    customer_phone = request.form.get('whatsapp_customer_phone')
    if not customer_name or not customer_phone:
        flash("Nome e telefone do cliente são obrigatórios.")
        return redirect(url_for('cart'))
    phone_digits = ''.join(filter(str.isdigit, customer_phone))
    cart_items, total_price = [], 0
    if 'cart' in session:
        for product_id, quantity in session['cart'].items():
            product = db.session.get(Product, int(product_id))
            if product:
                item_total = product.preco * quantity
                cart_items.append({'product': product, 'quantity': quantity, 'total': item_total})
                total_price += item_total
    if not cart_items:
        flash("Carrinho vazio.")
        return redirect(url_for('cart'))
    pedido_texto = [f"- {item['quantity']}x {item['product'].nome} ..... R$ {(item['product'].preco * item['quantity']):.2f}" for item in cart_items]
    pedido_formatado = "\n".join(pedido_texto)
    
    # *** ALTERAÇÃO FEITA AQUI ***
    pix_code = generate_pix_br_code(
        pix_key="jfsgranitos@gmail.com", # CHAVE PIX ATUALIZADA
        merchant_name="JFS REVESTIMENTOS",
        merchant_city="SAO PAULO",
        amount=total_price,
        txid="PEDIDOCLIENTE"
    )
    
    message = (
        f" prezado(a) *{customer_name}*,\n\n"
        f"Segue o seu pedido realizado com o vendedor *{current_user.username}*:\n\n"
        f"```\n{pedido_formatado}\n```\n"
        f"--------------------------------\n"
        f"*TOTAL:* R$ {total_price:.2f}\n\n"
        f"Para efetuar o pagamento, utilize a nossa chave PIX (E-mail):\n"
        f"🔑 *jfsgranitos@gmail.com*\n\n" # Chave PIX na mensagem também atualizada
        f"Ou pague diretamente pelo PIX Copia e Cola abaixo:\n"
        f"👇 *PIX Copia e Cola (com valor)* 👇\n"
        f"```\n{pix_code}\n```\n\n"
        f"Agradecemos a preferência!"
    )
    whatsapp_url = f"https://wa.me/55{phone_digits}?text={urllib.parse.quote(message)}"
    session.pop('cart', None)
    return redirect(whatsapp_url)

# --- FUNÇÃO DE CRIAÇÃO DO BANCO DE DADOS ---
def setup_database(app):
    with app.app_context():
        inspector = inspect(db.engine)
        if not inspector.has_table("user"):
            print("AVISO: Tabelas não encontradas. Criando novo banco de dados...")
            db.create_all()
            ARQUIVO_CSV = 'dados_iniciais.csv'
            df = pd.read_csv(ARQUIVO_CSV, encoding='latin-1')
            for index, row in df.iterrows():
                new_product = Product(nome=row['Nome'], preco=row['Preco'])
                db.session.add(new_product)
            users_to_add = [
                User(username='Junior', password=generate_password_hash('123', method='pbkdf2:sha256'), role='consulta'),
                User(username='Fabiane', password=generate_password_hash('190513', method='pbkdf2:sha256'), role='consulta'),
                User(username='Admin', password=generate_password_hash('Admin2580', method='pbkdf2:sha256'), role='admin')
            ]
            db.session.bulk_save_objects(users_to_add)
            db.session.commit()
            print("Banco de dados criado e populado com sucesso!")
        else:
            print("Banco de dados já existe. Nenhum dado novo foi inserido.")

# --- INICIADOR DA APLICAÇÃO ---
if __name__ == '__main__':
    setup_database(app)
    app.run(debug=True, use_reloader=False)