from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import jwt
import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Create the Flask application.
app = Flask(__name__)

# Secret key used to sign JWT tokens.
# In a real application, this should be stored in an environment variable.
app.config['SECRET_KEY'] = 'web_store_secret_key_2026'

# MySQL database connection.
#
# Format:
# mysql+pymysql://USERNAME:PASSWORD@HOST/DATABASE_NAME
#
# XAMPP commonly uses:
# username = root
# password = empty
# host = localhost
#
# If your MySQL root account has a password, add it after root:
# mysql+pymysql://root:YOUR_PASSWORD@localhost/web_store_db

app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mysql+pymysql://root:@localhost/web_store_db'
)

# Disable unnecessary modification tracking.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and connect it to Flask.
db = SQLAlchemy(app)


# ============================================================
# RATE LIMITING CONFIGURATION
# ============================================================

# Rate limiting prevents clients from sending too many requests
# to certain API endpoints within a short period.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
    headers_enabled=True
)


# ============================================================
# DATABASE MODELS
# ============================================================

# Each class represents a table in our MySQL database.
# SQLAlchemy uses these classes to create and manage records.


# ------------------------------------------------------------
# 1. USER MODEL
# ------------------------------------------------------------

class User(db.Model):

    __tablename__ = 'users'

    # Primary key: unique ID for each user.
    id = db.Column(db.Integer, primary_key=True)

    # Username must be unique.
    username = db.Column(db.String(100), unique=True, nullable=False)

    # We store a hashed password, never the original password.
    password = db.Column(db.String(255), nullable=False)

    # Available roles:
    # admin, advanced_user, simple_user
    role = db.Column(db.String(30), nullable=False, default='simple_user')

    created_at = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow
    )


# ------------------------------------------------------------
# 2. CLIENT MODEL
# ------------------------------------------------------------

class Client(db.Model):

    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)

    # Connects a client to their user account.
    # SET NULL in the database allows the client record to remain
    # if the associated user account is deleted.
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        unique=True,
        nullable=True
    )

    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(30))

    address = db.Column(db.String(255))
    city = db.Column(db.String(100))

    created_at = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow
    )

    # Relationship allows us to access the associated user.
    user = db.relationship('User', backref='client', uselist=False)


# ------------------------------------------------------------
# 3. CATEGORY MODEL
# ------------------------------------------------------------

class Category(db.Model):

    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)


# ------------------------------------------------------------
# 4. BRAND MODEL
# ------------------------------------------------------------

class Brand(db.Model):

    __tablename__ = 'brands'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), unique=True, nullable=False)


# ------------------------------------------------------------
# 5. GENDER MODEL
# ------------------------------------------------------------

class Gender(db.Model):

    __tablename__ = 'genders'

    id = db.Column(db.Integer, primary_key=True)

    # Men, Women or Children.
    name = db.Column(db.String(50), unique=True, nullable=False)


# ------------------------------------------------------------
# 6. SIZE MODEL
# ------------------------------------------------------------

class Size(db.Model):

    __tablename__ = 'sizes'

    id = db.Column(db.Integer, primary_key=True)

    # Examples: XS, S, M, L, XL, XXL.
    name = db.Column(db.String(20), unique=True, nullable=False)


# ------------------------------------------------------------
# 7. COLOR MODEL
# ------------------------------------------------------------

class Color(db.Model):

    __tablename__ = 'colors'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(50), unique=True, nullable=False)


# ------------------------------------------------------------
# 8. PRODUCT MODEL
# ------------------------------------------------------------

class Product(db.Model):

    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)

    # DECIMAL is appropriate for money because it avoids
    # floating-point rounding problems.
    price = db.Column(db.Numeric(10, 2), nullable=False)

    # This is the original stock quantity.
    # Current available stock will be calculated using orders.
    initial_quantity = db.Column(db.Integer, nullable=False, default=0)

    # Foreign keys connect the product with lookup tables.
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.id'),
        nullable=False
    )

    brand_id = db.Column(
        db.Integer,
        db.ForeignKey('brands.id'),
        nullable=False
    )

    gender_id = db.Column(
        db.Integer,
        db.ForeignKey('genders.id'),
        nullable=False
    )

    # Optional image URL for displaying the product in the frontend.
    image_url = db.Column(db.String(500))

    created_at = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow
    )

    # Relationships allow us to access related information easily.
    category = db.relationship('Category')
    brand = db.relationship('Brand')
    gender = db.relationship('Gender')

    # A product can have multiple sizes and colors.
    sizes = db.relationship(
        'Size',
        secondary='product_sizes',
        backref='products'
    )

    colors = db.relationship(
        'Color',
        secondary='product_colors',
        backref='products'
    )


# ------------------------------------------------------------
# 9. PRODUCT SIZES
# ------------------------------------------------------------

# This association table connects products with sizes.
# It represents a many-to-many relationship.
#
# Example:
# A T-shirt can have S, M, L and XL sizes.
# The same size M can belong to many different products.

class ProductSize(db.Model):

    __tablename__ = 'product_sizes'

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='CASCADE'),
        primary_key=True
    )

    size_id = db.Column(
        db.Integer,
        db.ForeignKey('sizes.id', ondelete='CASCADE'),
        primary_key=True
    )


# ------------------------------------------------------------
# 10. PRODUCT COLORS
# ------------------------------------------------------------

# This association table connects products with colors.
# One product can be available in several colors.

class ProductColor(db.Model):

    __tablename__ = 'product_colors'

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='CASCADE'),
        primary_key=True
    )

    color_id = db.Column(
        db.Integer,
        db.ForeignKey('colors.id', ondelete='CASCADE'),
        primary_key=True
    )


# ------------------------------------------------------------
# 11. DISCOUNT MODEL
# ------------------------------------------------------------

class Discount(db.Model):

    __tablename__ = 'discounts'

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='CASCADE'),
        nullable=False
    )

    # Example: 20 means 20% discount.
    discount_percentage = db.Column(db.Numeric(5, 2), nullable=False)

    # Discounts are active only between these dates.
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow
    )

    product = db.relationship('Product', backref='discounts')


# ------------------------------------------------------------
# 12. ORDER MODEL
# ------------------------------------------------------------

class Order(db.Model):

    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)

    client_id = db.Column(
        db.Integer,
        db.ForeignKey('clients.id'),
        nullable=False
    )

    total_amount = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    # Possible statuses:
    # pending, confirmed, completed, cancelled.
    status = db.Column(
        db.String(30),
        nullable=False,
        default='pending'
    )

    order_date = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow
    )

    client = db.relationship('Client', backref='orders')

    # One order can contain multiple order items.
    items = db.relationship(
        'OrderItem',
        backref='order',
        cascade='all, delete-orphan'
    )


# ------------------------------------------------------------
# 13. ORDER ITEM MODEL
# ------------------------------------------------------------

class OrderItem(db.Model):

    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey('orders.id', ondelete='CASCADE'),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id'),
        nullable=False
    )

    quantity = db.Column(db.Integer, nullable=False)

    # We save the product price at the moment of purchase.
    # If the product price changes later, old orders remain unchanged.
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    # The customer selects a size and color when ordering.
    size_id = db.Column(
        db.Integer,
        db.ForeignKey('sizes.id'),
        nullable=True
    )

    color_id = db.Column(
        db.Integer,
        db.ForeignKey('colors.id'),
        nullable=True
    )

    product = db.relationship('Product')
    size = db.relationship('Size')
    color = db.relationship('Color')


# ============================================================
# AUTHENTICATION AND ROLE-BASED ACCESS
# ============================================================


# ------------------------------------------------------------
# 1. TOKEN REQUIRED DECORATOR
# ------------------------------------------------------------

def token_required(f):
    """
    This decorator protects an API endpoint.

    It checks whether the request contains a valid JWT token.

    The frontend or Postman must send the token in this format:

    Authorization: Bearer YOUR_TOKEN

    If the token is valid, the username, role and user ID
    are stored in request.user so other decorators can use them.
    """

    @wraps(f)
    def decorated(*args, **kwargs):

        token = None

        # Read the Authorization header from the request.
        auth_header = request.headers.get('Authorization')

        # Check whether the header contains a Bearer token.
        if auth_header and auth_header.startswith('Bearer '):

            # Extract the token after "Bearer ".
            token = auth_header.split(' ', 1)[1]

        # If no token was provided, deny access.
        if not token:
            return jsonify({
                'message': 'Token is missing'
            }), 401

        try:

            # Decode the token using our secret key.
            # PyJWT automatically checks the expiration date.
            data = jwt.decode(
                token,
                app.config['SECRET_KEY'],
                algorithms=['HS256']
            )

            # Save the decoded information for the protected route.
            request.user = data

        except jwt.ExpiredSignatureError:

            return jsonify({
                'message': 'Token has expired. Please log in again.'
            }), 401

        except jwt.InvalidTokenError:

            return jsonify({
                'message': 'Token is invalid'
            }), 401

        # If the token is valid, continue to the original route.
        return f(*args, **kwargs)

    return decorated


# ------------------------------------------------------------
# 2. ADMIN REQUIRED DECORATOR
# ------------------------------------------------------------

def admin_required(f):
    """
    Only users with the admin role can access this endpoint.
    """

    @wraps(f)
    def decorated(*args, **kwargs):

        if request.user.get('role') != 'admin':

            return jsonify({
                'message': 'Admin access required'
            }), 403

        return f(*args, **kwargs)

    return decorated


# ------------------------------------------------------------
# 3. ADVANCED USER REQUIRED DECORATOR
# ------------------------------------------------------------

def advanced_required(f):
    """
    Allows both admin and advanced_user roles.

    This is useful for viewing orders and generating reports.
    """

    @wraps(f)
    def decorated(*args, **kwargs):

        allowed_roles = ['admin', 'advanced_user']

        if request.user.get('role') not in allowed_roles:

            return jsonify({
                'message': 'Admin or advanced user access required'
            }), 403

        return f(*args, **kwargs)

    return decorated


# ------------------------------------------------------------
# 4. PRODUCT MANAGER REQUIRED DECORATOR
# ------------------------------------------------------------

def product_manager_required(f):
    """
    Allows admins and advanced users to manage store products.

    Simple users cannot create, edit or delete inventory.
    """

    @wraps(f)
    def decorated(*args, **kwargs):

        allowed_roles = ['admin', 'advanced_user']

        if request.user.get('role') not in allowed_roles:

            return jsonify({
                'message': 'You are not authorized to manage products'
            }), 403

        return f(*args, **kwargs)

    return decorated


# ------------------------------------------------------------
# 5. REGISTER A NEW CUSTOMER
# ------------------------------------------------------------

@app.route('/auth/register', methods=['POST'])
def register():
    """
    Registers a new customer.

    The endpoint creates:
    1. A user account with the simple_user role.
    2. A client record containing customer information.

    A customer cannot choose their own role during registration.
    This prevents someone from registering as an administrator.

    Expected JSON:

    {
        "username": "customer1",
        "password": "password123",
        "first_name": "John",
        "last_name": "Smith",
        "email": "john@example.com",
        "phone": "070123456",
        "address": "Main Street 10",
        "city": "Skopje"
    }
    """

    # Read the JSON data sent by Postman or the frontend.
    data = request.get_json(silent=True) or {}

    # Extract account information.
    username = data.get('username')
    password = data.get('password')

    # Extract customer information.
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')

    phone = data.get('phone')
    address = data.get('address')
    city = data.get('city')

    # Check the required fields.
    if not all([username, password, first_name, last_name, email]):

        return jsonify({
            'message': 'Username, password, first name, last name and email are required'
        }), 400

    # Check whether the username already exists.
    existing_user = User.query.filter_by(username=username).first()

    if existing_user:

        return jsonify({
            'message': 'Username already exists'
        }), 409

    # Check whether the email already belongs to another client.
    existing_client = Client.query.filter_by(email=email).first()

    if existing_client:

        return jsonify({
            'message': 'Email already exists'
        }), 409

    # Create the user account.
    # Passwords are stored as hashes, not plain text.
    new_user = User(
        username=username,
        password=generate_password_hash(password),
        role='simple_user'
    )

    # Add the user first so MySQL generates the user ID.
    db.session.add(new_user)
    db.session.flush()

    # Create the customer record and connect it to the user.
    new_client = Client(
        user_id=new_user.id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        address=address,
        city=city
    )

    db.session.add(new_client)

    # Save both records in the database.
    db.session.commit()

    return jsonify({
        'message': 'Customer registered successfully',
        'user': {
            'id': new_user.id,
            'username': new_user.username,
            'role': new_user.role
        },
        'client': {
            'id': new_client.id,
            'first_name': new_client.first_name,
            'last_name': new_client.last_name,
            'email': new_client.email
        }
    }), 201


# ------------------------------------------------------------
# 6. LOGIN
# ------------------------------------------------------------

@app.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """
    Authenticates an existing user and returns a JWT.

    Expected JSON:

    {
        "username": "customer1",
        "password": "password123"
    }

    The JWT contains:
    - User ID
    - Username
    - Role
    - Expiration time (1 hour)
    """

    data = request.get_json(silent=True) or {}

    username = data.get('username')
    password = data.get('password')

    # Make sure both login fields were provided.
    if not username or not password:

        return jsonify({
            'message': 'Username and password are required'
        }), 400

    # Find the user by username.
    user = User.query.filter_by(username=username).first()

    # Check the password against the stored password hash.
    if user and check_password_hash(user.password, password):

        # Create a JWT containing the user's information.
        token = jwt.encode({

            'user_id': user.id,

            'username': user.username,

            'role': user.role,

            # The token expires one hour after it is created.
            'exp': datetime.datetime.now(datetime.timezone.utc)
                   + datetime.timedelta(hours=1)

        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({

            'message': 'Login successful',

            'token': token,

            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }

        }), 200

    # Return an error if the username or password is incorrect.
    return jsonify({
        'message': 'Invalid username or password'
    }), 401


# ------------------------------------------------------------
# 7. VIEW USERS - ADMIN ONLY
# ------------------------------------------------------------

@app.route('/api/users', methods=['GET'])
@token_required
@admin_required
def get_users():
    """
    Returns all registered users.

    Only admins can view user accounts.
    Password hashes are never included in the response.
    """

    users = User.query.all()

    users_list = []

    for user in users:

        users_list.append({

            'id': user.id,
            'username': user.username,
            'role': user.role,
            'created_at': user.created_at.isoformat()

        })

    return jsonify(users_list), 200


# ------------------------------------------------------------
# 8. CHANGE USER ROLE - ADMIN ONLY
# ------------------------------------------------------------

@app.route('/api/users/<int:user_id>/role', methods=['PUT'])
@token_required
@admin_required
def update_user_role(user_id):
    """
    Allows an admin to change another user's role.

    Expected JSON:

    {
        "role": "advanced_user"
    }
    """

    data = request.get_json(silent=True) or {}

    new_role = data.get('role')

    # Only these three roles are permitted.
    allowed_roles = ['admin', 'advanced_user', 'simple_user']

    if new_role not in allowed_roles:

        return jsonify({
            'message': 'Invalid role'
        }), 400

    # Find the user whose role should be changed.
    user = db.session.get(User, user_id)

    if not user:

        return jsonify({
            'message': 'User not found'
        }), 404

    # Update the user's role.
    user.role = new_role

    db.session.commit()

    return jsonify({
        'message': 'User role updated successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role
        }
    }), 200


# ============================================================
# PRODUCT HELPER FUNCTIONS
# ============================================================


# ------------------------------------------------------------
# 1. GET CURRENT PRODUCT QUANTITY
# ------------------------------------------------------------

def get_current_quantity(product_id):
    """
    Calculates the current available stock for a product.

    Formula:

    Initial Quantity - Sold Quantity = Current Quantity

    We count only products in confirmed or completed orders.

    Pending orders do not reduce stock.
    Cancelled orders do not reduce stock.
    """

    # Find the product.
    product = db.session.get(Product, product_id)

    if not product:
        return None

    # Calculate the total quantity ordered for this product.
    # The join connects order_items with orders.
    sold_quantity = db.session.query(
        db.func.coalesce(db.func.sum(OrderItem.quantity), 0)
    ).join(
        Order,
        OrderItem.order_id == Order.id
    ).filter(
        OrderItem.product_id == product_id,

        # Only confirmed and completed orders count as sold.
        Order.status.in_(['confirmed', 'completed'])
    ).scalar()

    # Calculate the available stock.
    current_quantity = product.initial_quantity - int(sold_quantity)

    return {
        'product_id': product.id,
        'name': product.name,
        'initial_quantity': product.initial_quantity,
        'sold_quantity': int(sold_quantity),
        'current_quantity': max(current_quantity, 0)
    }


# ------------------------------------------------------------
# 2. GET ACTIVE DISCOUNT
# ------------------------------------------------------------

def get_active_discount(product_id):
    """
    Returns the active discount percentage for a product.

    A discount is active when the current date is between
    its start_date and end_date.

    If there is no active discount, the function returns 0.
    """

    now = datetime.datetime.now()

    discount = Discount.query.filter(
        Discount.product_id == product_id,
        Discount.start_date <= now,
        Discount.end_date >= now
    ).order_by(
        Discount.discount_percentage.desc()
    ).first()

    if discount:
        return float(discount.discount_percentage)

    return 0


# ------------------------------------------------------------
# 3. FORMAT PRODUCT INFORMATION
# ------------------------------------------------------------

def product_to_dict(product):
    """
    Converts a Product database object into a dictionary.

    This makes it easier to return product information as JSON.

    Passwords and other private information are not involved here.
    """

    # Calculate the current stock.
    quantity_info = get_current_quantity(product.id)

    # Find the current active discount.
    discount_percentage = get_active_discount(product.id)

    # Calculate the discounted price.
    original_price = float(product.price)

    discounted_price = original_price * (
        1 - discount_percentage / 100
    )

    return {
        'id': product.id,
        'name': product.name,
        'description': product.description,

        'price': round(original_price, 2),
        'discount_percentage': discount_percentage,
        'discounted_price': round(discounted_price, 2),

        'initial_quantity': product.initial_quantity,
        'current_quantity': quantity_info['current_quantity'],

        'category': {
            'id': product.category.id,
            'name': product.category.name
        },

        'brand': {
            'id': product.brand.id,
            'name': product.brand.name
        },

        'gender': {
            'id': product.gender.id,
            'name': product.gender.name
        },

        'sizes': [
            {'id': size.id, 'name': size.name}
            for size in product.sizes
        ],

        'colors': [
            {'id': color.id, 'name': color.name}
            for color in product.colors
        ],

        'image_url': product.image_url,

        'created_at': product.created_at.isoformat()
    }


# ------------------------------------------------------------
# 4. VALIDATE PRODUCT REFERENCES
# ------------------------------------------------------------

def validate_product_references(data):
    """
    Checks whether the category, brand, gender, sizes and colors
    sent in a product request actually exist in the database.

    This prevents products from referring to nonexistent records.

    Expected IDs:
    category_id, brand_id, gender_id, size_ids, color_ids
    """

    category = db.session.get(Category, data.get('category_id'))
    brand = db.session.get(Brand, data.get('brand_id'))
    gender = db.session.get(Gender, data.get('gender_id'))

    if not category:
        return 'Category not found'

    if not brand:
        return 'Brand not found'

    if not gender:
        return 'Gender not found'

    # Sizes and colors are optional, but if IDs are provided,
    # every ID must exist in its respective table.
    size_ids = data.get('size_ids', [])
    color_ids = data.get('color_ids', [])

    if not isinstance(size_ids, list):
        return 'size_ids must be a list'

    if not isinstance(color_ids, list):
        return 'color_ids must be a list'

    existing_sizes = Size.query.filter(
        Size.id.in_(size_ids)
    ).all() if size_ids else []

    existing_colors = Color.query.filter(
        Color.id.in_(color_ids)
    ).all() if color_ids else []

    if len(existing_sizes) != len(set(size_ids)):
        return 'One or more sizes do not exist'

    if len(existing_colors) != len(set(color_ids)):
        return 'One or more colors do not exist'

    return None


# ============================================================
# PRODUCT API - GET ALL PRODUCTS
# ============================================================

@app.route('/api/products', methods=['GET'])
def get_products():
    """
    Returns all products in the store.

    No authentication required.

    Example:
    GET /api/products
    """

    # Retrieve all products from the database.
    products = Product.query.all()

    # Convert every product into a JSON-friendly dictionary.
    products_list = []

    for product in products:
        products_list.append(product_to_dict(product))

    return jsonify(products_list), 200


# ============================================================
# PRODUCT API - GET ONE PRODUCT
# ============================================================

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """
    Returns detailed information about one product.

    Example:
    GET /api/products/1
    """

    # Search for the product using its ID.
    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({
            'message': 'Product not found'
        }), 404

    return jsonify(product_to_dict(product)), 200


# ============================================================
# PRODUCT API - ADD PRODUCT
# ============================================================

@app.route('/api/products', methods=['POST'])
@token_required
@product_manager_required
def add_product():
    """
    Adds a new clothing product.

    Only admin and advanced_user can add products.

    The request must contain valid category, brand and gender IDs.
    """

    data = request.get_json(silent=True) or {}

    # Read the product information.
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    initial_quantity = data.get('initial_quantity')

    category_id = data.get('category_id')
    brand_id = data.get('brand_id')
    gender_id = data.get('gender_id')

    size_ids = data.get('size_ids', [])
    color_ids = data.get('color_ids', [])

    image_url = data.get('image_url')

    # Check that the required information was provided.
    if not all([
        name,
        price is not None,
        initial_quantity is not None,
        category_id,
        brand_id,
        gender_id
    ]):
        return jsonify({
            'message': 'Name, price, quantity, category, brand and gender are required'
        }), 400

    # Validate the numeric values.
    try:
        price = float(price)
        initial_quantity = int(initial_quantity)

        if price < 0 or initial_quantity < 0:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            'message': 'Price and quantity must be valid non-negative numbers'
        }), 400

    # Check that all referenced records exist.
    reference_error = validate_product_references(data)

    if reference_error:
        return jsonify({
            'message': reference_error
        }), 400

    # Create the product.
    new_product = Product(
        name=name,
        description=description,
        price=price,
        initial_quantity=initial_quantity,
        category_id=category_id,
        brand_id=brand_id,
        gender_id=gender_id,
        image_url=image_url
    )

    # Connect the selected sizes and colors.
    new_product.sizes = Size.query.filter(
        Size.id.in_(size_ids)
    ).all() if size_ids else []

    new_product.colors = Color.query.filter(
        Color.id.in_(color_ids)
    ).all() if color_ids else []

    # Save the product and its relationships.
    db.session.add(new_product)
    db.session.commit()

    return jsonify({
        'message': 'Product created successfully',
        'product': product_to_dict(new_product)
    }), 201


# ============================================================
# PRODUCT API - UPDATE PRODUCT
# ============================================================

@app.route('/api/products/<int:product_id>', methods=['PUT'])
@token_required
@product_manager_required
def update_product(product_id):
    """
    Updates an existing product.

    Only admin and advanced_user can edit products.

    PUT /api/products/1
    """

    # Find the product.
    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({
            'message': 'Product not found'
        }), 404

    data = request.get_json(silent=True) or {}

    # Update basic text fields only if they were provided.
    if 'name' in data:
        if not data['name']:
            return jsonify({'message': 'Product name cannot be empty'}), 400
        product.name = data['name']

    if 'description' in data:
        product.description = data['description']

    if 'image_url' in data:
        product.image_url = data['image_url']

    # Validate and update price.
    if 'price' in data:
        try:
            new_price = float(data['price'])

            if new_price < 0:
                raise ValueError

            product.price = new_price

        except (ValueError, TypeError):
            return jsonify({'message': 'Invalid product price'}), 400

    # Update original stock quantity.
    if 'initial_quantity' in data:
        try:
            new_quantity = int(data['initial_quantity'])

            if new_quantity < 0:
                raise ValueError

            # Do not allow the original stock to become smaller
            # than the number of units already sold.
            quantity_info = get_current_quantity(product.id)

            if new_quantity < quantity_info['sold_quantity']:
                return jsonify({
                    'message': 'Initial quantity cannot be less than the sold quantity'
                }), 400

            product.initial_quantity = new_quantity

        except (ValueError, TypeError):
            return jsonify({'message': 'Invalid stock quantity'}), 400

    # Validate category, brand and gender if any were changed.
    reference_fields = [
        'category_id',
        'brand_id',
        'gender_id',
        'size_ids',
        'color_ids'
    ]

    if any(field in data for field in reference_fields):

        # Build a complete reference dictionary using the existing
        # values for fields that were not included in the request.
        reference_data = {
            'category_id': data.get('category_id', product.category_id),
            'brand_id': data.get('brand_id', product.brand_id),
            'gender_id': data.get('gender_id', product.gender_id),
            'size_ids': data.get(
                'size_ids',
                [size.id for size in product.sizes]
            ),
            'color_ids': data.get(
                'color_ids',
                [color.id for color in product.colors]
            )
        }

        reference_error = validate_product_references(reference_data)

        if reference_error:
            return jsonify({'message': reference_error}), 400

        product.category_id = reference_data['category_id']
        product.brand_id = reference_data['brand_id']
        product.gender_id = reference_data['gender_id']

        if 'size_ids' in data:
            product.sizes = Size.query.filter(
                Size.id.in_(reference_data['size_ids'])
            ).all() if reference_data['size_ids'] else []

        if 'color_ids' in data:
            product.colors = Color.query.filter(
                Color.id.in_(reference_data['color_ids'])
            ).all() if reference_data['color_ids'] else []

    # Save the changes.
    db.session.commit()

    return jsonify({
        'message': 'Product updated successfully',
        'product': product_to_dict(product)
    }), 200


# ============================================================
# PRODUCT API - DELETE PRODUCT
# ============================================================

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_product(product_id):
    """
    Deletes a product.

    Only admins can delete products.

    We prevent deleting a product that already appears in an order,
    because order history should remain available.
    """

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({
            'message': 'Product not found'
        }), 404

    # Check whether the product has ever been ordered.
    existing_order_item = OrderItem.query.filter_by(
        product_id=product_id
    ).first()

    if existing_order_item:
        return jsonify({
            'message': 'This product belongs to an order and cannot be deleted'
        }), 409

    # Delete the product.
    db.session.delete(product)
    db.session.commit()

    return jsonify({
        'message': 'Product deleted successfully'
    }), 200


# ============================================================
# PRODUCT API - CURRENT QUANTITY
# ============================================================

@app.route('/api/products/<int:product_id>/quantity', methods=['GET'])
def get_product_quantity(product_id):
    """
    Returns the current available quantity of a product.

    Example:
    GET /api/products/1/quantity

    Formula:
    Initial Quantity - Confirmed/Completed Order Quantities
    = Current Quantity
    """

    # Call our helper function to calculate stock.
    quantity_info = get_current_quantity(product_id)

    if quantity_info is None:
        return jsonify({
            'message': 'Product not found'
        }), 404

    return jsonify(quantity_info), 200


# ============================================================
# PRODUCT API - APPLY DISCOUNT
# ============================================================

@app.route('/api/products/<int:product_id>/discount', methods=['POST'])
@token_required
@admin_required
def apply_discount(product_id):
    """
    Applies a discount to a product.

    Only admins can apply discounts.

    Expected JSON:

    {
        "discount_percentage": 20,
        "start_date": "2026-11-09 00:00:00",
        "end_date": "2026-11-30 23:59:59"
    }
    """

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({
            'message': 'Product not found'
        }), 404

    data = request.get_json(silent=True) or {}

    try:

        discount_percentage = float(data.get('discount_percentage'))

        start_date = datetime.datetime.strptime(
            data.get('start_date'),
            '%Y-%m-%d %H:%M:%S'
        )

        end_date = datetime.datetime.strptime(
            data.get('end_date'),
            '%Y-%m-%d %H:%M:%S'
        )

        if not 0 < discount_percentage <= 100:
            raise ValueError

        if end_date <= start_date:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            'message': 'Provide a valid discount percentage and date range'
        }), 400

    # Create a new discount record.
    new_discount = Discount(
        product_id=product_id,
        discount_percentage=discount_percentage,
        start_date=start_date,
        end_date=end_date
    )

    db.session.add(new_discount)
    db.session.commit()

    return jsonify({
        'message': 'Discount applied successfully',
        'product_id': product_id,
        'discount_percentage': discount_percentage,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    }), 201


# ============================================================
# PRODUCT API - ADVANCED SEARCH
# ============================================================

@app.route('/api/products/search', methods=['GET'])
def search_products():
    """
    Searches products using multiple optional filters.

    Supported query parameters:

    category
    gender
    brand
    price_min
    price_max
    size
    color
    availability

    Example:

    /api/products/search?gender=Women&brand=Nike&size=M
    &color=Red&price_min=20&price_max=100&availability=in_stock

    No authentication required.
    """

    # Start with all products.
    query = Product.query

    # Read the filters from the URL.
    category = request.args.get('category')
    gender = request.args.get('gender')
    brand = request.args.get('brand')

    size = request.args.get('size')
    color = request.args.get('color')

    price_min = request.args.get('price_min')
    price_max = request.args.get('price_max')

    availability = request.args.get('availability')

    # --------------------------------------------------------
    # FILTER BY CATEGORY
    # --------------------------------------------------------

    if category:
        query = query.join(Product.category).filter(
            Category.name.ilike(category)
        )

    # --------------------------------------------------------
    # FILTER BY GENDER
    # --------------------------------------------------------

    if gender:
        query = query.join(Product.gender).filter(
            Gender.name.ilike(gender)
        )

    # --------------------------------------------------------
    # FILTER BY BRAND
    # --------------------------------------------------------

    if brand:
        query = query.join(Product.brand).filter(
            Brand.name.ilike(brand)
        )

    # --------------------------------------------------------
    # FILTER BY MINIMUM PRICE
    # --------------------------------------------------------

    try:

        if price_min is not None:
            price_min = float(price_min)

            if price_min < 0:
                raise ValueError

            query = query.filter(Product.price >= price_min)

        # ----------------------------------------------------
        # FILTER BY MAXIMUM PRICE
        # ----------------------------------------------------

        if price_max is not None:
            price_max = float(price_max)

            if price_max < 0:
                raise ValueError

            query = query.filter(Product.price <= price_max)

        if price_min is not None and price_max is not None:
            if price_min > price_max:
                raise ValueError

    except ValueError:
        return jsonify({
            'message': 'Invalid price range'
        }), 400

    # --------------------------------------------------------
    # FILTER BY SIZE
    # --------------------------------------------------------

    if size:
        query = query.join(
            Product.sizes
        ).filter(
            Size.name.ilike(size)
        )

    # --------------------------------------------------------
    # FILTER BY COLOR
    # --------------------------------------------------------

    if color:
        query = query.join(
            Product.colors
        ).filter(
            Color.name.ilike(color)
        )

    # Remove duplicate products that may appear after joins.
    products = query.distinct().all()

    # --------------------------------------------------------
    # FILTER BY AVAILABILITY
    # --------------------------------------------------------

    # Stock is calculated dynamically because it depends
    # on confirmed and completed orders.
    if availability:

        if availability not in ['in_stock', 'out_of_stock']:
            return jsonify({
                'message': 'Availability must be in_stock or out_of_stock'
            }), 400

        filtered_products = []

        for product in products:

            quantity_info = get_current_quantity(product.id)

            current_quantity = quantity_info['current_quantity']

            if availability == 'in_stock' and current_quantity > 0:
                filtered_products.append(product)

            elif availability == 'out_of_stock' and current_quantity == 0:
                filtered_products.append(product)

        products = filtered_products

    # Convert the matching products into JSON.
    products_list = [
        product_to_dict(product)
        for product in products
    ]

    return jsonify({
        'total_results': len(products_list),
        'products': products_list
    }), 200


# ============================================================
# ORDER API - PLACE AN ORDER
# ============================================================

@app.route('/api/orders', methods=['POST'])
@token_required
def place_order():
    """
    Allows a logged-in customer to place an order.

    The customer is identified using the user ID in the JWT.

    Expected JSON:

    {
        "items": [
            {
                "product_id": 1,
                "quantity": 2,
                "size_id": 3,
                "color_id": 1
            }
        ]
    }

    New orders are created with the pending status.
    """

    # Find the client associated with the logged-in user.
    client = Client.query.filter_by(
        user_id=request.user['user_id']
    ).first()

    if not client:
        return jsonify({
            'message': 'Customer profile not found'
        }), 404

    data = request.get_json(silent=True) or {}

    items = data.get('items')

    # The order must contain at least one product.
    if not isinstance(items, list) or not items:
        return jsonify({
            'message': 'At least one order item is required'
        }), 400

    # Create the order first.
    new_order = Order(
        client_id=client.id,
        total_amount=0,
        status='pending'
    )

    db.session.add(new_order)

    # Flush sends the INSERT to MySQL so the order receives an ID.
    # We can then use this ID in the order_items table.
    db.session.flush()

    total_amount = 0

    # Process each product in the customer's order.
    for item in items:

        product_id = item.get('product_id')
        quantity = item.get('quantity')
        size_id = item.get('size_id')
        color_id = item.get('color_id')

        # Validate required information.
        if product_id is None or quantity is None:
            db.session.rollback()

            return jsonify({
                'message': 'Product ID and quantity are required'
            }), 400

        try:
            quantity = int(quantity)

            if quantity <= 0:
                raise ValueError

        except (ValueError, TypeError):
            db.session.rollback()

            return jsonify({
                'message': 'Quantity must be a positive integer'
            }), 400

        # Find the requested product.
        product = db.session.get(Product, product_id)

        if not product:
            db.session.rollback()

            return jsonify({
                'message': f'Product {product_id} not found'
            }), 404

        # Make sure the selected size belongs to this product.
        selected_size = None

        if size_id is not None:

            selected_size = db.session.get(Size, size_id)

            if not selected_size or selected_size not in product.sizes:
                db.session.rollback()

                return jsonify({
                    'message': 'Selected size is not available for this product'
                }), 400

        # Make sure the selected color belongs to this product.
        selected_color = None

        if color_id is not None:

            selected_color = db.session.get(Color, color_id)

            if not selected_color or selected_color not in product.colors:
                db.session.rollback()

                return jsonify({
                    'message': 'Selected color is not available for this product'
                }), 400

        # Calculate the current available quantity.
        quantity_info = get_current_quantity(product.id)

        # Check whether enough stock is available.
        if quantity > quantity_info['current_quantity']:
            db.session.rollback()

            return jsonify({
                'message': f'Not enough stock for {product.name}',
                'available_quantity': quantity_info['current_quantity']
            }), 400

        # Calculate the price after applying an active discount.
        discount_percentage = get_active_discount(product.id)

        original_price = float(product.price)

        unit_price = original_price * (
            1 - discount_percentage / 100
        )

        # Calculate the total for this order item.
        item_total = unit_price * quantity

        total_amount += item_total

        # Create the order item.
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=round(unit_price, 2),
            size_id=size_id,
            color_id=color_id
        )

        db.session.add(order_item)

    # Save the final order total.
    new_order.total_amount = round(total_amount, 2)

    # Save the order and all its items.
    db.session.commit()

    return jsonify({
        'message': 'Order placed successfully',
        'order': {
            'id': new_order.id,
            'client_id': new_order.client_id,
            'total_amount': float(new_order.total_amount),
            'status': new_order.status,
            'order_date': new_order.order_date.isoformat()
        }
    }), 201


# ============================================================
# ORDER API - GET ALL ORDERS
# ============================================================

@app.route('/api/orders', methods=['GET'])
@token_required
@advanced_required
def get_orders():
    """
    Returns all orders.

    Only admin and advanced_user can view all orders.
    """

    orders = Order.query.order_by(
        Order.order_date.desc()
    ).all()

    orders_list = []

    for order in orders:

        # Prepare the individual products in the order.
        items_list = []

        for item in order.items:

            items_list.append({
                'product_id': item.product_id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'size': item.size.name if item.size else None,
                'color': item.color.name if item.color else None
            })

        orders_list.append({

            'id': order.id,

            'client': {
                'id': order.client.id,
                'name': (
                    order.client.first_name + ' ' +
                    order.client.last_name
                ),
                'email': order.client.email
            },

            'total_amount': float(order.total_amount),
            'status': order.status,
            'order_date': order.order_date.isoformat(),

            'items': items_list
        })

    return jsonify(orders_list), 200


# ============================================================
# ORDER API - GET ONE ORDER
# ============================================================

@app.route('/api/orders/<int:order_id>', methods=['GET'])
@token_required
def get_order(order_id):
    """
    Returns the details of one order.

    Admin and advanced users can view any order.
    Simple users can view only their own orders.
    """

    order = db.session.get(Order, order_id)

    if not order:
        return jsonify({
            'message': 'Order not found'
        }), 404

    # Simple users must own the order they are requesting.
    if request.user['role'] == 'simple_user':

        client = Client.query.filter_by(
            user_id=request.user['user_id']
        ).first()

        if not client or order.client_id != client.id:
            return jsonify({
                'message': 'You are not authorized to view this order'
            }), 403

    items_list = []

    for item in order.items:

        items_list.append({

            'product_id': item.product_id,
            'product_name': item.product.name,
            'quantity': item.quantity,
            'unit_price': float(item.unit_price),

            'size': item.size.name if item.size else None,
            'color': item.color.name if item.color else None

        })

    return jsonify({

        'id': order.id,

        'client_id': order.client_id,

        'total_amount': float(order.total_amount),

        'status': order.status,

        'order_date': order.order_date.isoformat(),

        'items': items_list

    }), 200



# ============================================================
# CORRECTED ORDER API - UPDATE ORDER STATUS
# ============================================================

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@token_required
@advanced_required
def update_order_status(order_id):

    order = db.session.get(Order, order_id)

    if not order:
        return jsonify({'message': 'Order not found'}), 404

    data = request.get_json(silent=True) or {}
    new_status = data.get('status')

    allowed_statuses = [
        'pending', 'confirmed', 'completed', 'cancelled'
    ]

    if new_status not in allowed_statuses:
        return jsonify({'message': 'Invalid order status'}), 400

    if order.status in ['completed', 'cancelled']:
        return jsonify({
            'message': 'Completed or cancelled orders cannot be changed'
        }), 400

    # Check stock only when the order starts counting as sold.
    # An already-confirmed order is already included in the stock calculation.
    if (
        new_status in ['confirmed', 'completed']
        and order.status not in ['confirmed', 'completed']
    ):

        for item in order.items:

            quantity_info = get_current_quantity(item.product_id)

            if item.quantity > quantity_info['current_quantity']:
                return jsonify({
                    'message': 'Not enough stock to confirm this order',
                    'product_id': item.product_id,
                    'product_name': item.product.name,
                    'available_quantity': quantity_info['current_quantity'],
                    'requested_quantity': item.quantity
                }), 400

    order.status = new_status
    db.session.commit()

    return jsonify({
        'message': 'Order status updated successfully',
        'order_id': order.id,
        'new_status': order.status
    }), 200



# ============================================================
# LOOKUP TABLE API
# CATEGORIES, BRANDS, GENDERS, SIZES AND COLORS
# ============================================================

# This dictionary connects URL names with database models.
# For example, "categories" refers to the Category model.
LOOKUP_MODELS = {
    'categories': Category,
    'brands': Brand,
    'genders': Gender,
    'sizes': Size,
    'colors': Color
}


# ------------------------------------------------------------
# GET LOOKUP VALUES
# ------------------------------------------------------------

@app.route('/api/<resource>', methods=['GET'])
def get_lookup_values(resource):
    """
    Returns all records from a lookup table.

    Examples:
    GET /api/categories
    GET /api/brands
    GET /api/genders
    GET /api/sizes
    GET /api/colors

    These endpoints are public.
    """

    # Check whether the requested resource exists.
    model = LOOKUP_MODELS.get(resource)

    if not model:
        return jsonify({
            'message': 'Resource not found'
        }), 404

    # Retrieve all records from the selected table.
    records = model.query.order_by(model.id).all()

    # Convert the records into JSON dictionaries.
    results = []

    for record in records:

        item = {
            'id': record.id,
            'name': record.name
        }

        # Categories have an additional description field.
        if resource == 'categories':
            item['description'] = record.description

        results.append(item)

    return jsonify(results), 200


# ------------------------------------------------------------
# ADD LOOKUP VALUE
# ------------------------------------------------------------

@app.route('/api/<resource>', methods=['POST'])
@token_required
@admin_required
def add_lookup_value(resource):
    """
    Adds a new category, brand, gender, size or color.

    Only admins can add lookup values.

    Example:
    POST /api/categories

    JSON:
    {
        "name": "Hoodies",
        "description": "Comfortable hooded clothing"
    }
    """

    model = LOOKUP_MODELS.get(resource)

    if not model:
        return jsonify({
            'message': 'Resource not found'
        }), 404

    data = request.get_json(silent=True) or {}

    name = data.get('name')

    if not name or not name.strip():
        return jsonify({
            'message': 'Name is required'
        }), 400

    # Prevent duplicate names.
    existing = model.query.filter(
        db.func.lower(model.name) == name.strip().lower()
    ).first()

    if existing:
        return jsonify({
            'message': 'This value already exists'
        }), 409

    # Create the new record.
    if resource == 'categories':

        new_record = model(
            name=name.strip(),
            description=data.get('description')
        )

    else:

        new_record = model(name=name.strip())

    db.session.add(new_record)
    db.session.commit()

    return jsonify({
        'message': f'{resource.capitalize()} created successfully',
        'id': new_record.id,
        'name': new_record.name
    }), 201


# ------------------------------------------------------------
# UPDATE LOOKUP VALUE
# ------------------------------------------------------------

@app.route('/api/<resource>/<int:record_id>', methods=['PUT'])
@token_required
@admin_required
def update_lookup_value(resource, record_id):
    """
    Updates an existing lookup value.

    Example:
    PUT /api/categories/1

    JSON:
    {
        "name": "T-Shirts",
        "description": "Different types of T-shirts"
    }
    """

    model = LOOKUP_MODELS.get(resource)

    if not model:
        return jsonify({
            'message': 'Resource not found'
        }), 404

    record = db.session.get(model, record_id)

    if not record:
        return jsonify({
            'message': 'Record not found'
        }), 404

    data = request.get_json(silent=True) or {}

    if 'name' in data:

        if not isinstance(data['name'], str) or not data['name'].strip():
            return jsonify({'message': 'Name cannot be empty'}), 400

        # Check whether another record already uses this name.
        duplicate = model.query.filter(
            db.func.lower(model.name) == data['name'].strip().lower(),
            model.id != record_id
        ).first()

        if duplicate:
            return jsonify({
                'message': 'This name already exists'
            }), 409

        record.name = data['name'].strip()

    # Only categories have a description.
    if resource == 'categories' and 'description' in data:
        record.description = data['description']

    db.session.commit()

    return jsonify({
        'message': 'Record updated successfully',
        'id': record.id,
        'name': record.name
    }), 200


# ------------------------------------------------------------
# DELETE LOOKUP VALUE
# ------------------------------------------------------------

@app.route('/api/<resource>/<int:record_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_lookup_value(resource, record_id):
    """
    Deletes a lookup value.

    Only admins can delete lookup records.

    A value cannot be deleted if it is currently being used
    by a product or order.
    """

    model = LOOKUP_MODELS.get(resource)

    if not model:
        return jsonify({
            'message': 'Resource not found'
        }), 404

    record = db.session.get(model, record_id)

    if not record:
        return jsonify({
            'message': 'Record not found'
        }), 404

    # Check whether this lookup record is being used.
    if resource == 'categories':
        in_use = Product.query.filter_by(category_id=record_id).first()

    elif resource == 'brands':
        in_use = Product.query.filter_by(brand_id=record_id).first()

    elif resource == 'genders':
        in_use = Product.query.filter_by(gender_id=record_id).first()

    elif resource == 'sizes':
        in_use = ProductSize.query.filter_by(size_id=record_id).first()

        if not in_use:
            in_use = OrderItem.query.filter_by(size_id=record_id).first()

    else:
        in_use = ProductColor.query.filter_by(color_id=record_id).first()

        if not in_use:
            in_use = OrderItem.query.filter_by(color_id=record_id).first()

    if in_use:
        return jsonify({
            'message': 'This value is currently being used and cannot be deleted'
        }), 409

    db.session.delete(record)
    db.session.commit()

    return jsonify({
        'message': 'Record deleted successfully'
    }), 200


# ============================================================
# PRODUCT API - UPDATE STOCK
# ============================================================

@app.route('/api/products/<int:product_id>/stock', methods=['PUT'])
@token_required
@product_manager_required
def update_product_stock(product_id):
    """
    Updates the original stock quantity of a product.

    Only admin and advanced_user can update stock.

    Expected JSON:

    {
        "initial_quantity": 150
    }
    """

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({
            'message': 'Product not found'
        }), 404

    data = request.get_json(silent=True) or {}

    if 'initial_quantity' not in data:
        return jsonify({
            'message': 'initial_quantity is required'
        }), 400

    try:

        new_quantity = int(data['initial_quantity'])

        if new_quantity < 0:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            'message': 'Stock quantity must be a non-negative integer'
        }), 400

    # Calculate how many units have already been sold.
    quantity_info = get_current_quantity(product_id)

    if new_quantity < quantity_info['sold_quantity']:
        return jsonify({
            'message': 'Stock cannot be lower than the sold quantity'
        }), 400

    # Update the original stock quantity.
    product.initial_quantity = new_quantity

    db.session.commit()

    # Calculate the new current quantity.
    updated_quantity = get_current_quantity(product_id)

    return jsonify({
        'message': 'Stock updated successfully',
        'product_id': product_id,
        'initial_quantity': updated_quantity['initial_quantity'],
        'sold_quantity': updated_quantity['sold_quantity'],
        'current_quantity': updated_quantity['current_quantity']
    }), 200


# ============================================================
# REPORT API - DAILY EARNINGS
# ============================================================

@app.route('/api/reports/daily', methods=['GET'])
@token_required
@advanced_required
def daily_earnings():
    """
    Calculates total earnings for one day.

    Optional query parameter:
    date=YYYY-MM-DD

    Only confirmed and completed orders are included.
    """

    # Read the requested date.
    date_string = request.args.get('date')

    try:

        if date_string:
            selected_date = datetime.datetime.strptime(
                date_string,
                '%Y-%m-%d'
            ).date()

        else:
            selected_date = datetime.date.today()

    except ValueError:
        return jsonify({
            'message': 'Date must use YYYY-MM-DD format'
        }), 400

    # Calculate the total value of confirmed and completed orders
    # created on the selected date.
    result = db.session.query(
        db.func.coalesce(db.func.sum(Order.total_amount), 0)
    ).filter(
        db.func.date(Order.order_date) == selected_date,
        Order.status.in_(['confirmed', 'completed'])
    ).scalar()

    # Count the number of successful orders.
    order_count = Order.query.filter(
        db.func.date(Order.order_date) == selected_date,
        Order.status.in_(['confirmed', 'completed'])
    ).count()

    return jsonify({

        'report': 'Daily Earnings',

        'date': selected_date.isoformat(),

        'total_earnings': round(float(result), 2),

        'number_of_orders': order_count

    }), 200


# ============================================================
# REPORT API - MONTHLY EARNINGS
# ============================================================

@app.route('/api/reports/monthly', methods=['GET'])
@token_required
@advanced_required
def monthly_earnings():
    """
    Calculates total earnings for a selected month.

    Optional query parameters:
    year=2026
    month=11

    If no parameters are provided, the current month is used.
    """

    current_date = datetime.date.today()

    try:

        year = int(request.args.get('year', current_date.year))
        month = int(request.args.get('month', current_date.month))

        # Validate the year and month.
        if year < 2000 or month < 1 or month > 12:
            raise ValueError

    except ValueError:
        return jsonify({
            'message': 'Provide a valid year and month'
        }), 400

    # Calculate total earnings for the selected month.
    result = db.session.query(
        db.func.coalesce(db.func.sum(Order.total_amount), 0)
    ).filter(
        db.extract('year', Order.order_date) == year,
        db.extract('month', Order.order_date) == month,
        Order.status.in_(['confirmed', 'completed'])
    ).scalar()

    # Count successful orders for the month.
    order_count = Order.query.filter(
        db.extract('year', Order.order_date) == year,
        db.extract('month', Order.order_date) == month,
        Order.status.in_(['confirmed', 'completed'])
    ).count()

    return jsonify({

        'report': 'Monthly Earnings',

        'year': year,

        'month': month,

        'total_earnings': round(float(result), 2),

        'number_of_orders': order_count

    }), 200


# ============================================================
# REPORT API - TOP-SELLING PRODUCTS
# ============================================================

@app.route('/api/reports/top-products', methods=['GET'])
@token_required
@advanced_required
def top_selling_products():
    """
    Returns products ranked by the number of units sold.

    Only confirmed and completed orders are counted.

    Optional query parameter:
    limit=5
    """

    try:

        limit = int(request.args.get('limit', 5))

        if limit < 1 or limit > 100:
            raise ValueError

    except ValueError:
        return jsonify({
            'message': 'Limit must be between 1 and 100'
        }), 400

    # Join order_items with orders and products.
    # SUM calculates the total number of units sold per product.
    results = db.session.query(

        Product.id,
        Product.name,
        db.func.sum(OrderItem.quantity).label('total_sold')

    ).join(

        OrderItem,
        Product.id == OrderItem.product_id

    ).join(

        Order,
        OrderItem.order_id == Order.id

    ).filter(

        Order.status.in_(['confirmed', 'completed'])

    ).group_by(

        Product.id,
        Product.name

    ).order_by(

        db.func.sum(OrderItem.quantity).desc()

    ).limit(limit).all()

    products_list = []

    for result in results:

        products_list.append({

            'product_id': result.id,

            'product_name': result.name,

            'total_sold': int(result.total_sold)

        })

    return jsonify({

        'report': 'Top Selling Products',

        'products': products_list

    }), 200


# ============================================================
# USER API - CREATE USER
# ============================================================

@app.route('/api/users', methods=['POST'])
@token_required
@admin_required
def create_user():
    """
    Allows an admin to create a user account.

    This endpoint is intended for creating staff accounts
    and assigning their roles.

    Expected JSON:

    {
        "username": "new_advanced",
        "password": "password123",
        "role": "advanced_user"
    }
    """

    data = request.get_json(silent=True) or {}

    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'simple_user')

    if not username or not password:
        return jsonify({
            'message': 'Username and password are required'
        }), 400

    allowed_roles = [
        'admin',
        'advanced_user',
        'simple_user'
    ]

    if role not in allowed_roles:
        return jsonify({
            'message': 'Invalid user role'
        }), 400

    # Check whether the username is already in use.
    existing_user = User.query.filter_by(
        username=username
    ).first()

    if existing_user:
        return jsonify({
            'message': 'Username already exists'
        }), 409

    # Create the user and hash their password.
    new_user = User(
        username=username,
        password=generate_password_hash(password),
        role=role
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'message': 'User created successfully',
        'user': {
            'id': new_user.id,
            'username': new_user.username,
            'role': new_user.role
        }
    }), 201


# ============================================================
# USER API - DELETE USER
# ============================================================

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(user_id):
    """
    Allows an admin to delete a user account.

    Only admins can delete users.
    """

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            'message': 'User not found'
        }), 404

    # Prevent an administrator from accidentally deleting
    # the account currently being used for this request.
    if user.id == request.user['user_id']:
        return jsonify({
            'message': 'You cannot delete your own account'
        }), 400

    # Delete the account.
    # The clients table uses ON DELETE SET NULL, so an existing
    # customer record and its order history can remain.
    db.session.delete(user)
    db.session.commit()

    return jsonify({
        'message': 'User deleted successfully'
    }), 200


# ============================================================
# CUSTOM RATE LIMIT ERROR
# ============================================================

@app.errorhandler(429)
def ratelimit_error(error):
    """
    Returns a custom JSON response when a client exceeds
    the configured request limit.
    """

    return jsonify({
        'message': 'Rate limit exceeded. Please try again later.'
    }), 429


# ============================================================
# CUSTOM NOT FOUND ERROR
# ============================================================

@app.errorhandler(404)
def not_found_error(error):
    """
    Returns JSON instead of the default Flask HTML error page.
    """

    return jsonify({
        'message': 'The requested API endpoint was not found'
    }), 404


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

with app.app_context():

    # Create any database tables that do not already exist.
    # Existing tables and records are not deleted.
    db.create_all()

    # Check whether the users table is empty.
    if User.query.count() == 0:

        # Create an initial administrator account.
        admin_user = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin'
        )

        # Create an advanced user account.
        advanced_user = User(
            username='advanced',
            password=generate_password_hash('advanced123'),
            role='advanced_user'
        )

        # Save both accounts.
        db.session.add_all([
            admin_user,
            advanced_user
        ])

        db.session.commit()

        print('Initial users created successfully!')


# ==========================================
# FRONTEND ROUTE
# ==========================================

# Display the main web store page.
@app.route('/')
def home():
    return render_template('index.html')

# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == '__main__':

    # Start Flask's development server.
    app.run(debug=True)
