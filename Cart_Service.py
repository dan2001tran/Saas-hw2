import os
import requests
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import delete

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "cart.sqlite"
)
db = SQLAlchemy(app)


# Task Model
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


# Endpoint 1: (GET): Retrieve the current contents of a user’s shopping cart, including product names, quantities, and total prices.
@app.route("/cart/<int:user_id>", methods=["GET"])
def get_products_from_cart(user_id):
    cart = Cart.query.filter_by(userId=user_id).all()
    cart_products_list = [
        {
            "id": item.id,
            "userId": item.userId,
            "name": item.name,
            "price": item.price,
            "quantity": item.quantity,
        }
        for item in cart
    ]
    return jsonify({"items_in_cart": cart_products_list})


# Endpoint 2: (POST): Add a specified quantity of a product to the user’s cart.
@app.route("/cart/<int:user_id>/add/<int:product_id>", methods=["POST"])
def add_product_to_cart(user_id, product_id):
    data = request.json

    if "quantity" not in data:
        return jsonify({"error": "Quantity is missing"}), 400

    quantity = data["quantity"]

    payload = {"product_id": product_id, "quantity": quantity}
    response = requests.post(
        "https://cart-and-product-api.onrender.com/products/quantity/minus",
        json=payload,
    )

    if response.status_code != 200:
        return jsonify({"error": "Failed to update product quantity"}), 400

    existing_product = Cart.query.filter_by(userId=user_id, id=product_id).first()

    if existing_product:
        existing_product.quantity = existing_product.quantity + quantity
    else:
        new_product = Cart(
            id=product_id,
            name=response.json()["product"]["name"],
            userId=user_id,
            price=response.json()["product"]["price"],
            quantity=quantity,
        )
        db.session.add(new_product)

    db.session.commit()

    cart = Cart.query.filter_by(userId=user_id, id=product_id).first()
    if cart:
        return jsonify(
            {
                "message": "Added new item!",
                "id": cart.id,
                "user_id": cart.userId,
                "name": cart.name,
                "price": cart.price,
                "quantity": cart.quantity,
            }
        )
    else:
        return jsonify({"error": "cart item not found"}), 404


# Endpoint 3: (POST): Allow the addition of new grocery products to the inventory with information such as name, price, and quantity.
@app.route("/cart/<int:user_id>/remove/<int:product_id>", methods=["POST"])
def remove_product_to_cart(user_id, product_id):
    data = request.json

    if "quantity" not in data:
        return jsonify({"error": "Quantity is missing"}), 400

    quantity = data["quantity"]

    existing_product = Cart.query.filter_by(userId=user_id, id=product_id).first()

    if not existing_product:
        return jsonify({"error": "Product not found in cart"}), 404

    if existing_product.quantity > quantity:
        existing_product.quantity = existing_product.quantity - quantity
        payload = {"product_id": product_id, "quantity": quantity}
        response = requests.post(
            "https://cart-and-product-api.onrender.com/products/quantity/add",
            json=payload,
        )
    else:
        db.session.delete(existing_product)

        payload = {"product_id": product_id, "quantity": existing_product.quantity}
        response = requests.post(
            "https://cart-and-product-api.onrender.com/products/quantity/add",
            json=payload,
        )

        if response.status_code != 200:
            return (
                jsonify({"error": "Failed to update product quantity in inventory"}),
                400,
            )

    db.session.commit()

    return jsonify({"message": "Product quantity updated or removed from cart"})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5002, debug=True)
