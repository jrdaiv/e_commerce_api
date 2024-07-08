# E-Commerce API

This is a simple e-commerce API built using Flask and Marshmallow. The API allows you to manage products, customers, and orders.

## Features

- CRUD operations for products, customers, and orders
- Data validation and serialization using Marshmallow
- RESTful endpoints

## Technologies Used

- Flask
- Flask-SQLAlchemy
- Marshmallow
- Flask-CORS

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/ecommerce-api.git
    cd ecommerce-api
    ```

2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up the database:
    ```bash
    flask db init
    flask db migrate
    flask db upgrade
    ```

## Usage

1. Run the Flask application:
    ```bash
    flask run
    ```

2. The API will be available at `http://127.0.0.1:5000/`.

## API Endpoints

### Products

- `GET /products` - Get all products
- `GET /products/<id>` - Get a single product by ID
- `POST /products` - Create a new product
- `PUT /products/<id>` - Update a product by ID
- `DELETE /products/<id>` - Delete a product by ID

### Customers

- `GET /customers` - Get all customers
- `GET /customers/<id>` - Get a single customer by ID
- `POST /customers` - Create a new customer
- `PUT /customers/<id>` - Update a customer by ID
- `DELETE /customers/<id>` - Delete a customer by ID

### Orders

- `GET /orders` - Get all orders
- `GET /orders/<id>` - Get a single order by ID
- `POST /orders` - Create a new order
- `PUT /orders/<id>` - Update an order by ID
- `DELETE /orders/<id>` - Delete an order by ID

## Data Models

### Product

- `id` (Integer, Primary Key)
- `name` (String, Required)
- `description` (String)
- `price` (Float, Required)
- `quantity` (Integer, Required)

### Customer

- `id` (Integer, Primary Key)
- `name` (String, Required)
- `email` (String, Required, Unique)
- `phone` (String)

### Order

- `id` (Integer, Primary Key)
- `customer_id` (Integer, Foreign Key, Required)
- `product_id` (Integer, Foreign Key, Required)
- `quantity` (Integer, Required)
- `total_price` (Float, Required)

## License

This project is licensed under the MIT License. See the LICENSE file for details.
