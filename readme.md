# StyleStore – Clothing Web Store Application

## 1. Project Overview

StyleStore is a web-based clothing store application developed using Flask, MySQL, HTML, CSS, and JavaScript.

The application allows customers to browse clothing products, search and filter products, view available stock, add products to a shopping cart, and place orders.

It also provides administrative functionality for managing products, categories, brands, users, discounts, and orders. The application uses role-based access control to ensure that users can access only the operations permitted by their roles.

The backend is implemented as a RESTful API using Flask, while the frontend communicates with the backend through HTTP requests using JavaScript Fetch API.

## 2. Technologies Used

The project uses the following technologies:

| Technology | Purpose |
|---|---|
| Python | Main backend programming language |
| Flask | Backend web framework |
| Flask-SQLAlchemy | Database ORM |
| MySQL | Relational database |
| PyMySQL | MySQL database connection |
| PyJWT | JWT-based authentication |
| Werkzeug | Password hashing |
| Flask-Limiter | API rate limiting |
| HTML5 | Frontend structure |
| CSS3 | Frontend styling and responsive design |
| JavaScript | Frontend functionality and API communication |
| Postman | REST API testing |
| XAMPP / phpMyAdmin | Local MySQL database management |

## 3. Project Structure

The project has the following structure:

```text
web-store/
│
├── app.py                  # Flask application, models and REST APIs
│
├── templates/
│   └── index.html          # Main frontend page
│
├── static/
│   ├── css/
│   │   └── style.css       # Frontend styling
│   │
│   └── js/
│       └── app.js          # Frontend JavaScript and API requests
│
└── README.md               # Project documentation
```

## 4. Main Features

### Product Management
- Create new clothing products.
- Retrieve all products or a specific product.
- Update existing products.
- Delete products when they are not associated with existing orders.
- Update initial product stock.
- Display available product quantities.

### Product Categories and Attributes
The application supports managing:
- Categories
- Brands
- Genders
- Sizes
- Colors

These attributes are connected to products through relational database relationships.

### Product Search and Filtering
Customers can search and filter products using:
- Category
- Gender
- Brand
- Minimum and maximum price
- Size
- Color
- Product availability

Multiple filters can be combined in one request.

### Shopping Cart and Orders
- Add products to the shopping cart.
- Select product sizes and colors.
- Calculate the order total.
- Place customer orders.
- Retrieve order information.
- Confirm, complete, or cancel orders according to user permissions.

### Stock Management
The application calculates the current quantity of a product using:

```text
Current Quantity = Initial Quantity - Sold Quantity
```

Only confirmed and completed orders contribute to the sold quantity. Pending and cancelled orders do not reduce the available stock.

### Discounts
- Create product discounts.
- Specify discount percentages.
- Define discount start and end dates.
- Calculate discounted product prices automatically.

### Authentication and Authorization
The application uses JSON Web Tokens (JWT) for authentication.

Passwords are stored as hashes rather than plain text.

Three user roles are supported:

| Role | Permissions |
|---|---|
| Admin | Full administrative access, including product management, user management, discounts, orders, and reports |
| Advanced User | Product management, order management, and report access |
| Simple User | Customer-facing functionality, including browsing products, placing orders, and viewing personal orders |

Access to protected API endpoints is controlled using authentication and role-based authorization decorators.

### Reports
The application provides:
- Daily earnings reports.
- Monthly earnings reports.
- Top-selling products reports.

Reports are generated dynamically using order and order-item data.

## 5. Database Design

The application uses MySQL as its relational database.

Database name:

```text
web_store_db
```

The database contains the following main entities:

| Table / Entity | Description |
|---|---|
| User | Stores usernames, hashed passwords, and user roles |
| Client | Stores customer information associated with users |
| Product | Stores clothing product information and initial stock |
| Category | Stores product categories |
| Brand | Stores product brands |
| Gender | Stores gender classifications |
| Size | Stores available product sizes |
| Color | Stores available product colors |
| ProductSize | Connects products with available sizes |
| ProductColor | Connects products with available colors |
| Order | Stores customer orders and their statuses |
| OrderItem | Stores products, quantities, and prices belonging to orders |
| Discount | Stores product discounts and their validity periods |

The database uses primary keys and foreign keys to maintain relationships between entities.

Reports are calculated from order records rather than stored in separate report tables.

## 6. Installation and Project Setup

Follow these steps to run the application locally.

### Prerequisites

Make sure the following software is installed:

- Python 3.10 or newer.
- MySQL Server or XAMPP.
- phpMyAdmin (optional, for database management).
- Postman (for API testing).
- A code editor such as Visual Studio Code.

### Step 1: Clone the Repository

Open a terminal and run:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Navigate into the project directory:

```bash
cd web-store
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with the actual URL of your GitHub repository.

### Step 2: Install Dependencies

Install the required Python packages:

```bash
python -m pip install Flask Flask-SQLAlchemy PyJWT Flask-Limiter PyMySQL
```

### Step 3: Configure the MySQL Database

1. Open XAMPP Control Panel.
2. Start Apache and MySQL.
3. Open phpMyAdmin at:

```text
http://localhost/phpmyadmin
```

4. Create a new database named:

```text
web_store_db
```

5. Open the database connection configuration in `app.py`.

Example configuration:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mysql+pymysql://root:@localhost/web_store_db'
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
```

If your MySQL root account has a password, update the connection string accordingly:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mysql+pymysql://root:YOUR_PASSWORD@localhost/web_store_db'
)
```

Replace `YOUR_PASSWORD` with your actual MySQL password.

### Step 4: Initialize the Database

The application uses SQLAlchemy to create database tables.

When the application starts, the following operation initializes the database:

```python
db.create_all()
```

If the database is empty, the application also creates initial administrative and advanced user accounts.

The tables are created automatically based on the SQLAlchemy models defined in the application.

**Note:** `db.create_all()` creates missing tables but does not automatically update existing table structures when models change.

### Step 5: Run the Flask Application

From the project directory, execute:

```bash
python app.py
```

The Flask development server should start successfully.

Open the application in your browser:

```text
http://127.0.0.1:5000/
```

The StyleStore homepage should appear.

## 7. Default Test Accounts

The application initializes the following accounts when the user table is empty:

| Username | Password | Role |
|---|---|---|
| admin | admin123 | Admin |
| advanced | advanced123 | Advanced User |

Customers can create their own accounts through the registration endpoint.

**Important:** These are development credentials. Change the default passwords and use a secure secret key before deploying the application.

## 8. REST API Documentation

All API endpoints are available through the Flask backend.

Base URL:

```text
http://127.0.0.1:5000
```

Protected endpoints require a JWT token in the Authorization header:

```text
Authorization: Bearer YOUR_JWT_TOKEN
```

The API accepts and returns JSON data.

### 8.1 Authentication

| Method | Endpoint | Description | Access |
|---|---|---|---|
| POST | `/auth/register` | Register a new customer | Public |
| POST | `/auth/login` | Authenticate a user and receive a JWT token | Public |

Example login request:

```json
{
    "username": "admin",
    "password": "admin123"
}
```

Example registration request:

```json
{
    "username": "customer1",
    "password": "customer123",
    "first_name": "Test",
    "last_name": "Customer",
    "email": "customer1@example.com"
}
```

The login endpoint returns an authentication token that must be included in subsequent protected requests.

### 8.2 Product Management

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/products` | Retrieve all products | Public |
| GET | `/api/products/<product_id>` | Retrieve a specific product | Public |
| POST | `/api/products` | Create a product | Product manager |
| PUT | `/api/products/<product_id>` | Update a product | Product manager |
| DELETE | `/api/products/<product_id>` | Delete a product | Admin |
| GET | `/api/products/<product_id>/quantity` | Retrieve current stock information | Public |
| PUT | `/api/products/<product_id>/stock` | Update initial product stock | Product manager |
| POST | `/api/products/<product_id>/discount` | Create a product discount | Admin |

Example product creation request:

```json
{
    "name": "Basic Black Hoodie",
    "description": "Comfortable black cotton hoodie",
    "price": 35.99,
    "initial_quantity": 20,
    "category_id": 1,
    "brand_id": 1,
    "gender_id": 1,
    "size_ids": [1, 2, 3],
    "color_ids": [1],
    "image_url": "https://example.com/black-hoodie.jpg"
}
```

Example stock update request:

```json
{
    "initial_quantity": 30
}
```

Example discount creation request:

```json
{
    "discount_percentage": 10,
    "start_date": "2026-11-09 00:00:00",
    "end_date": "2026-11-30 23:59:59"
}
```

### 8.3 Product Search

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/products/search` | Search and filter products |

Supported query parameters:

| Parameter | Description |
|---|---|
| `category_id` | Filter by category |
| `gender_id` | Filter by gender |
| `brand_id` | Filter by brand |
| `price_min` | Minimum product price |
| `price_max` | Maximum product price |
| `size_id` | Filter by size |
| `color_id` | Filter by color |
| `availability` | Filter by product availability |

Example:

```text
GET /api/products/search?category_id=1&gender_id=1&price_min=20&price_max=50
```

Multiple query parameters can be combined to perform advanced product searches.

### 8.4 Categories, Brands, Genders, Sizes, and Colors

The application provides common CRUD operations for managing lookup data.

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/categories` | Retrieve categories | Public |
| POST | `/api/categories` | Create category | Admin |
| PUT | `/api/categories/<id>` | Update category | Admin |
| DELETE | `/api/categories/<id>` | Delete category | Admin |
| GET | `/api/brands` | Retrieve brands | Public |
| POST | `/api/brands` | Create brand | Admin |
| PUT | `/api/brands/<id>` | Update brand | Admin |
| DELETE | `/api/brands/<id>` | Delete brand | Admin |
| GET | `/api/genders` | Retrieve genders | Public |
| POST | `/api/genders` | Create gender | Admin |
| PUT | `/api/genders/<id>` | Update gender | Admin |
| DELETE | `/api/genders/<id>` | Delete gender | Admin |
| GET | `/api/sizes` | Retrieve sizes | Public |
| POST | `/api/sizes` | Create size | Admin |
| PUT | `/api/sizes/<id>` | Update size | Admin |
| DELETE | `/api/sizes/<id>` | Delete size | Admin |
| GET | `/api/colors` | Retrieve colors | Public |
| POST | `/api/colors` | Create color | Admin |
| PUT | `/api/colors/<id>` | Update color | Admin |
| DELETE | `/api/colors/<id>` | Delete color | Admin |

Example category creation request:

```json
{
    "name": "Hoodies",
    "description": "Comfortable hooded clothing"
}
```

### 8.5 Order Management

| Method | Endpoint | Description | Access |
|---|---|---|---|
| POST | `/api/orders` | Place a new order | Authenticated user |
| GET | `/api/orders` | Retrieve all orders | Advanced User / Admin |
| GET | `/api/orders/<order_id>` | Retrieve an individual order | Owner / Advanced User / Admin |
| PUT | `/api/orders/<order_id>/status` | Update order status | Advanced User / Admin |

Example order creation request:

```json
{
    "items": [
        {
            "product_id": 1,
            "quantity": 2,
            "size_id": 1,
            "color_id": 1
        }
    ]
}
```

Example order status update:

```json
{
    "status": "confirmed"
}
```

Supported order statuses:

- `pending`
- `confirmed`
- `completed`
- `cancelled`

The application validates product availability and order quantities before accepting orders.

### 8.6 Reports

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/reports/daily` | Generate daily earnings report | Advanced User / Admin |
| GET | `/api/reports/monthly` | Generate monthly earnings report | Advanced User / Admin |
| GET | `/api/reports/top-products` | Retrieve top-selling products | Advanced User / Admin |

Example requests:

```text
GET /api/reports/daily?date=2026-11-09
```

```text
GET /api/reports/monthly?year=2026&month=11
```

```text
GET /api/reports/top-products?limit=5
```

### 8.7 User Management

| Method | Endpoint | Description | Access |
|---|---|---|---|
| POST | `/api/users` | Create a user | Admin |
| DELETE | `/api/users/<user_id>` | Delete a user | Admin |

Example user creation request:

```json
{
    "username": "advanced2",
    "password": "password123",
    "role": "advanced_user"
}
```

Supported roles:

- `admin`
- `advanced_user`
- `simple_user`

## 9. Testing the Application

The REST API was tested using Postman.

The following functionality was tested:

- User registration and login.
- JWT authentication.
- Role-based access control.
- Product creation, retrieval, updating, and deletion.
- Category and attribute management.
- Product search and filtering.
- Product stock management.
- Product discounts.
- Customer order creation.
- Order retrieval and status updates.
- Stock calculation after order confirmation.
- Daily and monthly earnings reports.
- Top-selling products reports.
- Invalid requests and permission restrictions.

The frontend was tested through a web browser and verified to communicate with the Flask backend.

## 10. Running the Frontend

The frontend is served directly by Flask using its template and static-file functionality.

No separate frontend development server is required.

After starting the Flask application, open:

```text
http://127.0.0.1:5000/
```

The JavaScript frontend automatically retrieves products and categories from the backend.

Customers can:
- Browse products.
- Search for products.
- View product prices and discounts.
- Select sizes and colors.
- Add products to the shopping cart.
- Log in.
- Place orders.

## 11. Security and Validation

The application includes several security and validation mechanisms:

- Password hashing using Werkzeug.
- JWT authentication for protected endpoints.
- Role-based authorization.
- Validation of product references and order information.
- Stock availability checks.
- Restrictions on deleting records that are associated with existing orders or products.
- API rate limiting.
- Error handling for invalid requests and unauthorized access.

## 12. Future Improvements

Possible future improvements include:

- Customer registration directly from the frontend.
- Persistent shopping carts.
- An administrative dashboard.
- Product image uploads.
- Order history and tracking for customers.
- More advanced search and filtering options.
- Improved frontend product details and checkout experience.
- Deployment to a production hosting environment.

## 13. Author

Developed as a Web Services and Applications course project.

**Technologies:** Python, Flask, MySQL, HTML, CSS, JavaScript, REST API, JWT.
