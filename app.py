from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import delete, select
from sqlalchemy.orm import relationship, Session, DeclarativeBase, Mapped, mapped_column
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask import Flask, jsonify, request
from marshmallow import ValidationError, fields
from typing import List
import datetime

app = Flask(__name__)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root:Lunaluna24!@localhost/e_commerce_api_db"

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)
ma = Marshmallow(app)



class Customer(Base):
    __tablename__ = "Customers"
    customer_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(150), nullable=False)
    email: Mapped[str] = mapped_column(db.String(150), nullable=False)
    phone: Mapped[str] = mapped_column(db.String(30))

    customer_account: Mapped["CustomerAccount"] = relationship(back_populates="customer")
    orders: Mapped[List["Order"]] = relationship(back_populates="customer")

class CustomerAccount(Base):
    __tablename__ = "Customer_Accounts"
    account_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(db.String(150), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(db.String(150), nullable=False)

    customer_id: Mapped[int] = mapped_column(db.ForeignKey("Customers.customer_id"))
    customer: Mapped["Customer"] = relationship(back_populates="customer_account")

order_product = db.Table(
    "Order_Product", 
    Base.metadata,
    db.Column("order_id", db.ForeignKey("Orders.order_id"), primary_key=True),
    db.Column("product_id", db.ForeignKey("Products.product_id"), primary_key=True)      
)
class Order(Base):
    __tablename__ = "Orders"
    order_id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column(db.Date, nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey("Customers.customer_id"))
    customer: Mapped["Customer"] = relationship(back_populates="orders")
    products: Mapped[List["Product"]] = relationship(secondary=order_product)

    def make_order(self,product_id):
        self.products.append(product_id)
        db.session.commit()

class Product(Base):
    __tablename__ = "Products"
    product_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(150), nullable=False)
    price: Mapped[float] = mapped_column(db.Float, nullable=False)

with app.app_context():
    db.create_all()

#=======================================================================================

class CustomerSchema(ma.Schema):
    customer_id = fields.Integer()
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String()

    class Meta:
        fields = ("customer_id", "name", "email", "phone")

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

@app.route("/customers", methods=["POST"])
def add_customers():
    try:
        customer_data = customer_schema.load(request.json)
    except ValueError as err:
        return jsonify(err.messages), 400
    with Session(db.engine) as session:
        with session.begin():
            name = customer_data["name"]
            email = customer_data["email"]
            phone = customer_data["phone"]
            new_customer = Customer(name=name, email=email, phone=phone)
            session.add(new_customer)
            session.commit()
    return jsonify({"Message": "New Customer Has Been Successfully Added! "})



@app.route("/customers", methods=["GET"])
def get_customers():
    query = select(Customer)
    result = db.session.execute(query).scalars()
    customers = result.all()
    return customers_schema.jsonify(customers)



@app.route("/customers/<int:id>", methods=["PUT"])
def update_customer(id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Customer).filter(Customer.customer_id == id)
            result = session.execute(query).scalars().first()
            if result is None:
                return jsonify({"Message": "Customer Is Not Found! "}), 404
            customer = result
            try:
                customer_data = customer_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            for field, value in customer_data.items():
                setattr(customer, field, value)
            session.commit()
    return jsonify({"Message": " Customer Details Have Been Successfully Update! "}), 200



@app.route("/customers/<int:id>", methods=["DELETE"])
def delete_customer(id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Customer).filter(Customer.customer_id == id)
            result = session.execute(query).scalars().first()
            if result is None:
                return jsonify({"Error": " Customer Is Not Found! "}), 404
            session.delete(result)
        return jsonify({"Message": "Customer Has Been Successfully Removed! "})

#=========================================================================================

class AccountSchema(ma.Schema):
    account_id = fields.Integer(required=True)
    username = fields.String(required=True)
    password = fields.String(required=True)
    customer_id = fields.Integer(required=True)

    class Meta:
        fields = ("account_id", "username", "password")

account_schema = AccountSchema()
accounts_schema = AccountSchema(many=True)

@app.route('/customer_account', methods=['POST'])
def add_customer_account():
    try:
        customer_account_data = account_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    with Session(db.engine) as session:
        with session.begin():
            username = customer_account_data["username"]
            password = customer_account_data["password"]
            customer_id = customer_account_data["customer_id"]
            new_account = CustomerAccount(username=username, password=password, customer_id=customer_id)
            session.add(new_account)
            session.commit()

    return jsonify({"Message": "New Customer Has Been Successfully Added! "}), 201


@app.route('/customer_account/<int:account_id>', methods=['GET'])
def get_customer_account(account_id):
    with Session(db.engine) as session:
        query = select(CustomerAccount).filter_by(account_id=account_id)
        result = session.execute(query).scalars().first()
        if result is None:
            return jsonify({"Message": "Customer Was Not Found! "})
        return account_schema.jsonify(result)

@app.route('/customer_account/<int:account_id>', methods=['PUT'])
def update_customer_account(account_id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(CustomerAccount).filter_by(account_id=account_id)
            result = session.execute(query).scalars().first()
            if result in None:
                return jsonify({"Message": "Custome Was Not Found! "})
            customer = result
            try:
                customer_account_data = account_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            customer.username = customer_account_data["username"]
            customer.password = customer_account_data["password"]
            customer.customer_id = customer_account_data["customer_id"]
            session.commit()
    return jsonify({"Message": "Customer Account Updated Successfully!"}), 200

@app.route('/customer_account/<int:account_id>', methods=['DELETE'])
def delete_customer_account(account_id):
    with Session(db.engine) as session:
        query = select(CustomerAccount).filter_by(account_id=account_id)
        result = session.execute(query).scalars().first()
        if result is None:
            return jsonify({"Message": "Customer Not Found!"}), 404
        session.delete(result)
        session.commit()
        return jsonify({"Message": "Customer Account Deleted Successfully!"}), 200

#====================================================================================================

class ProductSchema(ma.Schema):
    product_id = fields.Integer(required=True)
    name = fields.String(required=True)
    price = fields.Integer(required=True)

    class Meta:
        fields = ("product_id", "name", "price")

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

@app.route('/products', methods=['POST'])
def add_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    with Session(db.engine) as session:
        with session.begin():
            new_product = Product(name=product_data["name"],price=product_data["price"])
            session.add(new_product)
            session.commit()
    return jsonify({"Message": "New Product Has Been Successfully Added! "}), 201

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product():
    query = select(Product)
    result = db.session.execute(query).scalars().all()
    products = result.all()
    return product_schema.jsonify(products)

@app.route('/product/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Product).filter(Product.product_id == product_id)
            result = session.execute(query).scalars()
            # print(result)
            if result is None:
                return jsonify({"Error": "Product Was Not Found! "}), 404
            product = result
            try:
                product_data = product_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            for field, value in product_data.item():
                setattr(product, field, value)
            session.commit()
            return jsonify({"Message": f"Product For {product_id} Has Update Successfully  "})

@app.route('/product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    delete_statement = delete(Product).where(Product.product_id == product_id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"Error": f"Product With Id Of {product_id} Doesn't Exist! "}), 404
        return jsonify({"Message": "Product Has Now Been Deleted! "}), 200
    
@app.route('/products', methods=['GET'])
def list_products():
    with Session(db.engine) as session:
        query = select(Product)
        result = session.execute(query).scalars().all()
        products = result
        return products_schema.jsonify(products)

#========================================================================================================

class OrderSchema(ma.Schema):
    order_id = fields.Integer(required=True)
    customer_id = fields.Integer(required=True)
    date = fields.Date(required=True)
    product_id = fields.List(fields.Integer(), required=False)

    class Meta:
        fields = ("order_id", "customer_id", "date", "product_id")

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)


@app.post("/orders")
def add_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    product_ids = order_data.get("product_id", [])
    new_order = Order(
        customer_id=order_data["customer_id"],
        date=order_data["date"]
    )

    with Session(db.engine) as session:
        with session.begin():
            for product_id in product_ids:
                product = session.query(Product).get(product_id)
                if product:
                    new_order.products.append(product)
            session.add(new_order)
            session.commit()
    return jsonify({"Message": "Order Has Added Successfully! "})

@app.get("/orders")
def get_orders():
    query = select(Order)
    result = db.session.execute(query).scalars().all()
    orders_with_products = []
    orders = result
    for order in orders:
        order_dict = {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "date": order.date,
            "product": [product.product_id for product in order.products]
        }
        orders_with_products.append(order_dict)
    return jsonify(orders_with_products)


@app.put("/orders/<int:order_id>")
def update_orders(order_id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Order).filter(Order.order_id == order_id)
            result = session.execute(query).scalar()
            if result in None:
                return jsonify({"Message": "Order Was Not Found! "})
            order = result
            try:
                order_data = order_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            order.customer_id = order_data.get("customer_id", order.customer_id)
            order.date = order_data.get("date", order.date)
            product_ids = order_data.get("product_id", [])
            order.products.clear()
            for product_id in product_ids:
                product = session.query(Product).get(product_id)
                if product:
                    order.products.append(product)
            session.commit()
            return jsonify({"Message": f"Order With Id if {order_id} Has Been Successfully Updated! "})

@app.delete("/orders/<int:order_id>")
def delete_order(order_id):
    delete_statement = delete(Order).where(Order.order_id == order_id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"Error": f"Order With Id {order_id} Doesn't Exist! "})
        return jsonify({"Message": "Order Has Been Deleted! "})


@app.route("/")
def home():
    return "<h1> This Is My Api I Just Created!! ㄟ( ▔, ▔ )ㄏ </h1>" 



if __name__ == "__main__":
    app.run(debug=True)

