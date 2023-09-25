import os

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import delete

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "product.sqlite"
)
db = SQLAlchemy(app)


# Task Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


# Endpoint 1: (GET): Retrieve a list of available grocery products, including their names, prices, and quantities in stock.
@app.route("/products", methods=["GET"])
def get_products():
    products = Product.query.all()
    products_list = [
        {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": product.quantity,
        }
        for product in products
    ]
    return jsonify({"products": products_list})


# Endpoint 2: (GET): Get details about a specific product by its unique ID.
@app.route("/products/<int:product_id>", methods=["GET"])
def get_specific_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(
            {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "quantity": product.quantity,
            }
        )
    else:
        return jsonify({"error": "product not found"}), 404


# Endpoint 3: (POST): Allow the addition of new grocery products to the inventory with information such as name, price, and quantity.
@app.route("/products", methods=["POST"])
def create_product():
    data = request.json
    if "name" not in data:
        return jsonify({"error": "Name"}), 400
    if "price" not in data:
        return jsonify({"error": "Price is missing"}), 400
    if "quantity" not in data:
        return jsonify({"error": "Quanity is missing"}), 400

    new_product = Product(
        id=data["product_id"],
        name=data["name"],
        price=data["price"],
        quantity=data["quantity"],
    )
    db.session.add(new_product)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Product created",
                "product": {
                    "id": new_product.id,
                    "name": new_product.name,
                    "price": new_product.price,
                    "quantity": new_product.quantity,
                },
            }
        ),
        201,
    )


# Endpoint 4: (Post): Add to the quantity of a specific product by its unique ID.
@app.route("/products/quantity/add", methods=["POST"])
def add_product_quantity():
    data = request.json
    if "product_id" not in data:
        return jsonify({"error": "product_id is missing"}), 400
    if "quantity" not in data:
        return jsonify({"error": "Quanity is missing"}), 400
    ##
    product_id = data["product_id"]
    amount = data["quantity"]
    product = Product.query.get(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    product.quantity = product.quantity + amount
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Product quantity updated",
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "quantity": product.quantity,
                },
            }
        ),
        200,
    )


# Endpoint 5: (Post): Subtract the quantity of a specific product by its unique ID.
@app.route("/products/quantity/minus", methods=["POST"])
def minus_product_quantity():
    data = request.json
    if "product_id" not in data:
        return jsonify({"error": "product_id is missing"}), 400
    if "quantity" not in data:
        return jsonify({"error": "Quanity is missing"}), 400
    ##
    product_id = data["product_id"]
    amount = data["quantity"]
    product = Product.query.get(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    if product.quantity < amount:
        return jsonify({"error": "There is not enough product"}), 404
    else:
        product.quantity = product.quantity - amount
        db.session.commit()

    return (
        jsonify(
            {
                "message": "Product quantity updated",
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "quantity": product.quantity,
                },
            }
        ),
        200,
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
