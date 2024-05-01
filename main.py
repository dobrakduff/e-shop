# Commit 1: Added SQLAlchemy model for Product
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import abort
from sqlalchemy.ext.declarative import DeclarativeMeta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clothing_shop.db'
db = SQLAlchemy(app)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    photo = db.Column(db.String(100))


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('cart_items', lazy=True))
    quantity = db.Column(db.Integer, nullable=False, default=1)


# Commit 2: Initialized Flask app and SQLAlchemy


with app.app_context():
    db.create_all()


# Commit 3: Defined routes


@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart_item = CartItem(product=product)
    db.session.add(cart_item)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/", methods=["GET", "POST"])
def home():
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

@app.route('/remove_from_cart/<int:cart_item_id>', methods=['POST'])
def remove_from_cart(cart_item_id):
    cart_item = CartItem.query.get_or_404(cart_item_id)
    db.session.delete(cart_item)
    db.session.commit()
    return redirect(url_for('view_cart'))



# Commit 4: Added basic functionality to routes

# Commit 5: Ran Flask application if executed directly
if __name__ == "__main__":
    app.run(debug=True)
