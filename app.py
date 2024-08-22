import os
from flask import Flask, jsonify, request 
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session 
from sqlalchemy import select, delete 
from flask_marshmallow import Marshmallow
from flask_cors import CORS 
import datetime
from typing import List 
from marshmallow import ValidationError, fields, validate




app = Flask(__name__)
CORS(app) 
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('DATABASE_URL') # = "mysql+mysqlconnector://root:Lunaluna24!@localhost/e_commerce_api_db"

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(app, model_class=Base) 

ma = Marshmallow(app) 


class Customer(Base): 
    __tablename__ = "Customers"     
    customer_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(320), nullable=False)
    phone: Mapped[str] = mapped_column(db.String(15))
    customer_account: Mapped["CustomerAccount"] = db.relationship(back_populates="customer")
    orders: Mapped[List["Order"]] = db.relationship(back_populates="customer")
    def __str__(self):
        return {"customer_id": self.customer_id, "name": self.name, "email": self.email, "phone":self.phone}


class CustomerAccount(Base):
    __tablename__ = "Customer_Accounts"
    account_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(db.String(255), nullable = False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('Customers.customer_id'))
    customer: Mapped["Customer"] = db.relationship(back_populates="customer_account")

order_product = db.Table(
    "Order_Product", 
    Base.metadata,
    db.Column("order_id", db.ForeignKey("Orders.order_id"), primary_key=True),
    db.Column("product_id", db.ForeignKey("Products.product_id"), primary_key=True)      
)

class Order(Base):
    __tablename__ = "Orders"

    order_id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column(db.Date, nullable = False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey("Customers.customer_id"))
    customer: Mapped["Customer"] = db.relationship(back_populates="orders")
    products: Mapped[List["Product"]] = db.relationship(secondary=order_product)

class Product(Base):
    __tablename__ = "Products"
    product_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    price: Mapped[float] = mapped_column(db.Float, nullable=False)

with app.app_context():
    db.create_all() 


class CustomerSchema(ma.Schema):
    customer_id = fields.Integer()
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        fields = ("customer_id", "email", "name", "phone")

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

@app.route("/customers", methods = ["GET"])
def get_customers():
    query = select(Customer)  
    result = db.session.execute(query).scalars() 
    customers = result.all() 
    for customer in customers:
        for order in customer.orders:
            print(order.products) 
    return customers_schema.jsonify(customers)

@app.route("/customers", methods = ["POST"])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400 
    with Session(db.engine) as session: 
        with session.begin(): 
            name = customer_data['name']
            email = customer_data['email']
            phone = customer_data['phone']
            new_customer = Customer(name=name, email=email, phone=phone) 
            session.add(new_customer)
            session.commit()
    return jsonify({"Message": "Created customer"}), 201

    
@app.route("/customers/<int:id>", methods=["PUT"])
def update_customer(id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Customer).filter(Customer.customer_id == id)
            result = session.execute(query).scalars().first()
            if result is None:
                return jsonify({"message": "Customer not found"}), 404 
            customer = result
            try: 
                customer_data = customer_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400 
            for field, value in customer_data.items():
                setattr(customer, field, value)

            session.commit() 

    return jsonify({"message": "Customer details updated successfully"}), 200 


@app.route("/customers/<int:id>", methods=["DELETE"])
def delete_customer(id):
    with Session(db.engine) as session:
        print(id)
        with session.begin():
            query = select(Customer).filter(Customer.customer_id == id)
            result = session.execute(query).scalars().first()
            if result is None:
                return jsonify({"Error": " Customer Is Not Found! "}), 404
            session.delete(result)
        return jsonify({"Message": "Customer Has Been Successfully Removed! "})

class ProductSchema(ma.Schema):
    product_id = fields.Integer(required=False)
    name = fields.String(required=True, validate=validate.Length(min=1))
    price = fields.Float(required=True, validate=validate.Range(min=0))

    class Meta:
        fields = ("product_id", "name", "price")

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)


@app.route('/products', methods=["POST"])
def add_product():
    try:

        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400 

    with Session(db.engine) as session:
        with session.begin():

            new_product = Product(name=product_data['name'], price=product_data['price'])
            session.add(new_product)
            session.commit()

    return jsonify({"Message": "New product successfully added!"}), 201 
@app.route('/products', methods=["GET"])
def get_products():
    query = select(Product) 
    result = db.session.execute(query).scalars()
    products = result.all()

    return products_schema.jsonify(products)

@app.route("/products/<int:product_id>", methods=["GET"])
def get_product_by_id(product_id):
    query = select(Product).filter(Product.product_id == product_id)
    result = db.session.execute(query).scalar()
    print(result)
    if result is None:
        return jsonify({"error": "Product not found"}), 404 
    product = result
    try:
        
        return product_schema.jsonify(product)
    except ValidationError as err:
        return jsonify(err.messages), 400 

@app.route("/products/by-name", methods=["GET"])
def get_product_by_name():
    name = request.args.get("name")
    search = f"%{name}%" #% is a wildcard
    # use % with LIKE to find partial matches
    query = select(Product).where(Product.name.like(search)).order_by(Product.price.asc())

    products = db.session.execute(query).scalars().all()
    print(products)

    return product_schema.jsonify(products)

@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Product).filter(Product.product_id == product_id)
            result = session.execute(query).scalar() 
            print(result)            
            
            if result is None:
                return jsonify({"error": "Product not found!"}), 404
            product = result
            try:
                product_data = product_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            for field, value in product_data.items():
                setattr(product, field, value)

            session.commit()
            return jsonify({"message": "Product details succesfully updated!"}), 200 
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    # breakpoint()
    delete_statement = delete(Product).where(Product.product_id==product_id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"error" "Product not found"}), 404
        
        return jsonify({"message": "Product successfully deleted!"}), 200

class OrderSchema(ma.Schema):
    order_id = fields.Integer(required=False)
    customer_id = fields.Integer(required=True)
    date = fields.Date(required=True)
    products = fields.List(fields.Nested(ProductSchema))

    class Meta:
        fields = ("order_id", "customer_id", "date", "products")
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

@app.route("/orders", methods=["POST"])
def add_order():
    try:
        json_order = request.json
        products = json_order.pop('products', [])
        if not products:
            return jsonify({"Error": "Cannot place an order without products"}), 400

        # Validate the order data excluding products
        order_data = order_schema.load(json_order)
    except ValidationError as err:
        # If there's a validation error, return a 400 response with error messages
        return jsonify(err.messages), 400

    # Create a new session
    with Session(db.engine) as session:
        with session.begin():
            # Create a new order instance
            new_order = Order(customer_id=order_data['customer_id'], date=order_data['date'])

            # Populate order products using product IDs passed in via JSON
            for id in products:
                product = session.execute(select(Product).filter(Product.product_id == id)).scalar()
                if product:
                    print(new_order.products)
                    new_order.products.append(product)
                    session.add(new_order)
                    session.commit()
                    return jsonify({"message": "Order was successfully placed!"}), 201
                else:
                    return jsonify({"Error": f"Product with ID {id} not found"}), 404


@app.route("/orders", methods=["GET"])
def get_orders():
    query = select(Order)
    result = db.session.execute(query).scalars()
    products = result.all()
    return orders_schema.jsonify(products)
@app.route("/orders/<int:order_id>", methods=["GET"])
def get_orders_by_id(order_id):
    query = select(Order).filter(Order.order_id==order_id)
    result = db.session.execute(query).scalars()
    if result is None:
            return jsonify({"message": "Order Not Found"}), 404
    order = result.all()
    try:
        return orders_schema.jsonify(order)
    except ValidationError as err:
            #if we error let them know
            return jsonify(err.messages), 400


@app.route('/orders/<int:order_id>', methods=["PUT"])
def update_order(order_id):
    try:
        json_order = request.json
        products = json_order.pop('products', None)
        
        # Validate the order data excluding products
        order_data = order_schema.load(json_order, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    with Session(db.engine) as session:
        with session.begin():
            query = select(Order).filter(Order.order_id == order_id)
            result = session.execute(query).scalar()
            if result is None:
                return jsonify({"message": "Order Not Found"}), 404
            
            order = result
            
            for field, value in order_data.items():
                setattr(order, field, value)
            
            # If products are provided, update the products associated with the order
            if products is not None:
                order.products.clear()
                for id in products:
                    product = session.execute(select(Product).filter(Product.product_id == id)).scalar()
                    if product:
                        order.products.append(product)
                    else:
                        return jsonify({"Error": f"Product with ID {id} not found"}), 404

            session.commit()
            
    return jsonify({"message": "Order was successfully updated!"}), 200
        
@app.route("/orders/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    delete_statement = delete(Order).where(Order.order_id==order_id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"error": "Order not found" }), 404
        return jsonify({"message": "Order removed successfully"}), 200






    

    










@app.route("/")
def home():
    return "<h1>This a tasty api (ヘ･_･)ヘ┳━┳  (╯°□°）╯︵ ┻━┻</h1>"



if __name__ == "__main__": #check that the file we're in is the file thats being run
    app.run(debug=True) #if so we run our application and turn on the debugger



