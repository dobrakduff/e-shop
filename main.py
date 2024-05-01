from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
import os
import warnings


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clothing_shop.db'
app.config['SECRET_KEY'] = 'pudge22211'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['UPLOAD_FOLDER'] = 'static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
login_manager = LoginManager(app)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    photo = db.Column(db.String(100))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    product = db.relationship('Product')
    quantity = db.Column(db.Integer, nullable=False, default=1)


with app.app_context():
    db.create_all()

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@app.route('/add_to_cart/<int:product_id>', methods=['GET', 'POST'])
def add_to_cart(product_id):
    if request.method == 'POST':
        product = Product.query.get_or_404(product_id)
        cart_item = CartItem(product=product)
        db.session.add(cart_item)
        db.session.commit()
        return redirect(url_for('home'))  # Redirect to the home page or wherever appropriate
    else:
        # Handle GET request if needed
        pass


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if request.method == 'POST':
        # Handle form submission to add a new product
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        photo = request.files['photo']

        if photo and allowed_file(photo.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
            photo.save(filename)

            new_product = Product(name=name, price=price, description=description, photo=photo.filename)
            db.session.add(new_product)
            db.session.commit()

    products = Product.query.all()
    return render_template('admin_panel.html', products=products)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('admin_panel'))
    return render_template('login.html')


@app.before_request
def check_admin():
    if request.endpoint == 'admin_panel' and (not current_user.is_authenticated or current_user.username != 'admin'):
        return redirect(url_for('login'))


@login_manager.user_loader
def load_user(user_id):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecationWarning)
        return User.query.get(int(user_id))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    # Find the product by id
    product = Product.query.get_or_404(product_id)

    # Delete the associated image file from the file system
    if product.photo:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], product.photo))
        except FileNotFoundError:
            # Handle the case where the file does not exist
            pass

    # Delete the product from the database
    db.session.delete(product)
    db.session.commit()

    return redirect(url_for('admin_panel'))


@app.route("/", methods=["GET", "POST"])
def home():
    sort_by = request.args.get('sort_by', 'default')

    if sort_by == 'price_asc':
        products = Product.query.order_by(Product.price).all()
    elif sort_by == 'price_desc':
        products = Product.query.order_by(Product.price.desc()).all()
    else:
        products = Product.query.all()

    return render_template('index.html', products=products)


@app.route('/cart')
def view_cart():
    cart_items = CartItem.query.all()
    return render_template('cart.html', cart_items=cart_items)


@app.route('/product/<int:product_id>')
def product_details(product_id):
    product = Product.query.get(product_id)
    if product:
        return render_template('product_details.html', product=product)
    else:
        return "Product not found", 404


@app.route('/checkout', methods=['POST'])
def checkout():
    # Delete the first cart item
    first_cart_item = CartItem.query.first()
    db.session.delete(first_cart_item)

    # Fetch all remaining cart items
    remaining_cart_items = CartItem.query.all()

    # Decrement the IDs of remaining cart items by 1
    for cart_item in remaining_cart_items:
        cart_item.id -= 1

    # Commit the changes
    db.session.commit()

    # Redirect the user to a confirmation page or any other appropriate page
    return redirect(url_for('view_cart'))


@app.route('/remove_from_cart/<int:cart_item_id>', methods=['POST'])
def remove_from_cart(cart_item_id):
    cart_item = CartItem.query.get_or_404(cart_item_id)
    db.session.delete(cart_item)
    db.session.commit()
    return redirect(url_for('view_cart'))


@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    # Find the product by id
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        # Update product details based on form submission
        product.name = request.form['name']
        product.price = request.form['price']
        product.description = request.form['description']

        # Save changes to the database
        db.session.commit()

        return redirect(url_for('admin_panel'))

    # Render the edit product form with the product details
    return render_template('edit_product.html', product=product)


if __name__ == "__main__":
    app.run(debug=True)
