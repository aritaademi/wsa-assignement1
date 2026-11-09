
// =====================================================
// STYLESTORE - FRONTEND JAVASCRIPT
// =====================================================

// Base URL of our Flask backend.
// Since Flask serves both the frontend and backend,
// we can use relative API paths.
const API_URL = "";

// Store the JWT token after a successful login.
let authToken = localStorage.getItem("authToken");

// Store the products currently displayed.
let products = [];

// Store products added to the shopping cart.
let cart = [];


// =====================================================
// HELPER FUNCTIONS
// =====================================================

// Get the JSON response from an API request.
// If the request fails, display the backend error message.
async function apiRequest(url, options = {}) {

    // Add JSON headers to every request.
    const headers = {
        "Content-Type": "application/json",
        ...options.headers
    };

    // Add the JWT token when the user is logged in.
    if (authToken) {
        headers["Authorization"] = `Bearer ${authToken}`;
    }

    // Send the request to Flask.
    const response = await fetch(API_URL + url, {
        ...options,
        headers
    });

    // Convert the response into JSON.
    const data = await response.json().catch(() => ({}));

    // Handle unsuccessful responses.
    if (!response.ok) {
        throw new Error(
            data.message || data.error || "Something went wrong."
        );
    }

    return data;
}


// Extract an array from API responses.
// This supports APIs returning either an array directly
// or an object containing products, categories, or data.
function getArray(data, possibleKeys = []) {

    if (Array.isArray(data)) {
        return data;
    }

    for (const key of possibleKeys) {
        if (Array.isArray(data[key])) {
            return data[key];
        }
    }

    return [];
}


// Convert product size/color data into a consistent format.
// Our backend may return variants as objects or ID values.
function normalizeVariants(variants) {

    if (!Array.isArray(variants)) {
        return [];
    }

    return variants.map(item => {

        if (typeof item === "object" && item !== null) {
            return {
                id: item.id,
                name: item.name
            };
        }

        return {
            id: item,
            name: String(item)
        };
    });
}


// =====================================================
// LOAD CATEGORIES
// =====================================================

async function loadCategories() {

    try {

        // Request all categories from Flask.
        const data = await apiRequest("/api/categories");

        const categories = getArray(data, ["categories", "data"]);

        const categoryList = document.getElementById("categoryList");

        // Remove old category elements.
        categoryList.replaceChildren();

        // Display each category.
        categories.forEach(category => {

            const categoryElement = document.createElement("div");

            categoryElement.className = "category-item";

            categoryElement.textContent = category.name;

            categoryList.appendChild(categoryElement);

        });

    } catch (error) {

        console.error("Error loading categories:", error);

        document.getElementById("categoryList").textContent =
            "Unable to load categories.";

    }
}


// =====================================================
// LOAD PRODUCTS
// =====================================================

async function loadProducts(searchTerm = "") {

    try {

        // Request products from the backend.
        // The name parameter is optional.
        let url = "/api/products";

        if (searchTerm.trim() !== "") {
            url = "/api/products/search?name=" +
                encodeURIComponent(searchTerm.trim());
        }

        const data = await apiRequest(url);

        products = getArray(data, ["products", "data", "results"]);

        // Apply a client-side name filter as well.
        // This ensures searching works even if the backend
        // does not implement the name parameter.
        if (searchTerm.trim() !== "") {

            const search = searchTerm.trim().toLowerCase();

            products = products.filter(product =>
                product.name.toLowerCase().includes(search)
            );

        }

        displayProducts();

    } catch (error) {

        console.error("Error loading products:", error);

        document.getElementById("productList").textContent =
            "Unable to load products.";

    }
}


// =====================================================
// DISPLAY PRODUCTS
// =====================================================

function displayProducts() {

    const productList = document.getElementById("productList");

    // Remove previous product cards.
    productList.replaceChildren();

    // Display a message if no products exist.
    if (products.length === 0) {

        productList.textContent = "No products found.";

        return;
    }

    // Create a card for every product.
    products.forEach(product => {

        const card = document.createElement("div");

        card.className = "product-card";

        // Product image.
        const image = document.createElement("img");

        image.src = product.image_url || "";
        image.alt = product.name;
        image.loading = "lazy";

        // Use a placeholder if the image cannot load.
        image.addEventListener("error", () => {
            image.style.display = "none";
        });

        // Product name.
        const name = document.createElement("h3");

        name.textContent = product.name;

        // Product description.
        const description = document.createElement("p");

        description.textContent =
            product.description || "No description available.";

        // Product price.
        const price = document.createElement("p");

        const originalPrice = Number(product.price);

        const discountedPrice = Number(
            product.discounted_price ?? product.price
        );

        // Show the original and discounted prices when applicable.
        if (discountedPrice < originalPrice) {

            price.innerHTML =
                `<del>${originalPrice.toFixed(2)}</del> ` +
                `<strong>${discountedPrice.toFixed(2)}</strong>`;

        } else {

            price.textContent = originalPrice.toFixed(2);

        }

        // Available quantity.
        const stock = document.createElement("p");

        const availableQuantity = Number(product.current_quantity ?? 0);

        stock.textContent = `Available: ${availableQuantity}`;

        // Size selector.
        const sizeSelect = document.createElement("select");

        sizeSelect.appendChild(
            new Option("Select size", "")
        );

        const sizes = normalizeVariants(product.sizes);

        sizes.forEach(size => {

            sizeSelect.appendChild(
                new Option(size.name, size.id)
            );

        });

        // Color selector.
        const colorSelect = document.createElement("select");

        colorSelect.appendChild(
            new Option("Select color", "")
        );

        const colors = normalizeVariants(product.colors);

        colors.forEach(color => {

            colorSelect.appendChild(
                new Option(color.name, color.id)
            );

        });

        // Add to cart button.
        const addButton = document.createElement("button");

        addButton.className = "primary-button";

        addButton.textContent = "Add to Cart";

        // Disable the button if there is no available stock
        // or if the product has no selectable variants.
        addButton.disabled =
            availableQuantity <= 0 ||
            sizes.length === 0 ||
            colors.length === 0;

        // Add the selected product to the cart.
        addButton.addEventListener("click", () => {

            addToCart(
                product,
                sizeSelect.value,
                colorSelect.value
            );

        });

        // Add all elements to the product card.
        card.append(
            image,
            name,
            description,
            price,
            stock,
            sizeSelect,
            colorSelect,
            addButton
        );

        productList.appendChild(card);

    });

}


// =====================================================
// SHOPPING CART
// =====================================================

function addToCart(product, sizeId, colorId) {

    // The user must select a size and color.
    if (!sizeId || !colorId) {

        alert("Please select a size and color.");

        return;
    }

    // Check current quantity before adding an item.
    const quantityInCart = cart
        .filter(item => item.product_id === product.id)
        .reduce((total, item) => total + item.quantity, 0);

    const availableQuantity = Number(product.current_quantity ?? 0);

    if (quantityInCart + 1 > availableQuantity) {

        alert("Not enough stock available.");

        return;
    }

    // Check whether this exact product, size, and color
    // combination already exists in the cart.
    const existingItem = cart.find(item =>
        item.product_id === product.id &&
        item.size_id === Number(sizeId) &&
        item.color_id === Number(colorId)
    );

    if (existingItem) {

        // Increase the quantity if the item already exists.
        existingItem.quantity++;

    } else {

        // Otherwise create a new cart item.
        cart.push({

            product_id: product.id,

            name: product.name,

            price: Number(
                product.discounted_price ?? product.price
            ),

            size_id: Number(sizeId),

            color_id: Number(colorId),

            quantity: 1

        });

    }

    updateCart();

    alert("Product added to cart!");

}


// =====================================================
// UPDATE SHOPPING CART DISPLAY
// =====================================================

function updateCart() {

    const cartItems = document.getElementById("cartItems");

    const cartCount = document.getElementById("cartCount");

    const cartTotal = document.getElementById("cartTotal");

    // Clear the previous cart display.
    cartItems.replaceChildren();

    // Calculate total number of individual items.
    const totalItems = cart.reduce(
        (total, item) => total + item.quantity,
        0
    );

    cartCount.textContent = totalItems;

    // Calculate the total price.
    const totalPrice = cart.reduce(
        (total, item) => total + item.price * item.quantity,
        0
    );

    cartTotal.textContent = totalPrice.toFixed(2);

    // Display each item.
    cart.forEach((item, index) => {

        const itemElement = document.createElement("div");

        itemElement.className = "cart-item";

        const description = document.createElement("p");

        description.textContent =
            `${item.name} | Size ID: ${item.size_id} | ` +
            `Color ID: ${item.color_id} | ` +
            `Quantity: ${item.quantity} | ` +
            `Price: ${(item.price * item.quantity).toFixed(2)}`;

        // Button for removing an item.
        const removeButton = document.createElement("button");

        removeButton.textContent = "Remove";

        removeButton.addEventListener("click", () => {

            cart.splice(index, 1);

            updateCart();

        });

        itemElement.append(description, removeButton);

        cartItems.appendChild(itemElement);

    });

}


// =====================================================
// LOGIN
// =====================================================

// Open the login modal.
document.getElementById("loginButton").addEventListener("click", () => {

    document.getElementById("loginModal").classList.remove("hidden");

});


// Close the login modal.
document.getElementById("closeLogin").addEventListener("click", () => {

    document.getElementById("loginModal").classList.add("hidden");

});


// Handle login form submission.
document.getElementById("loginForm").addEventListener("submit", async event => {

    // Prevent the page from refreshing.
    event.preventDefault();

    const username = document.getElementById("username").value;

    const password = document.getElementById("password").value;

    const message = document.getElementById("loginMessage");

    try {

        // Send login information to Flask.
        const data = await apiRequest("/auth/login", {

            method: "POST",

            body: JSON.stringify({

                username: username,

                password: password

            })

        });

        // Save the returned JWT token.
        authToken = data.token;

        localStorage.setItem("authToken", authToken);

        message.textContent = "Login successful!";

        message.style.color = "green";

        // Close the modal after a short delay.
        setTimeout(() => {

            document.getElementById("loginModal").classList.add("hidden");

            document.getElementById("loginForm").reset();

        }, 800);

    } catch (error) {

        message.textContent = error.message;

        message.style.color = "red";

    }

});


// =====================================================
// LOGOUT
// =====================================================

// Add a logout button to the navigation dynamically.
const logoutButton = document.createElement("button");

logoutButton.textContent = "Logout";

logoutButton.className = "nav-button";

logoutButton.addEventListener("click", () => {

    // Remove the saved token.
    localStorage.removeItem("authToken");

    authToken = null;

    alert("You have been logged out.");

});

document.querySelector(".nav-links").appendChild(logoutButton);


// =====================================================
// SHOW CART
// =====================================================

document.getElementById("cartButton").addEventListener("click", () => {

    const cartSection = document.getElementById("cartSection");

    cartSection.classList.toggle("hidden");

    // Scroll to the cart section.
    if (!cartSection.classList.contains("hidden")) {

        cartSection.scrollIntoView({
            behavior: "smooth"
        });

    }

});


// =====================================================
// SEARCH PRODUCTS
// =====================================================

document.getElementById("searchButton").addEventListener("click", () => {

    const searchTerm = document.getElementById("searchInput").value;

    loadProducts(searchTerm);

});


// Also allow searching by pressing Enter.
document.getElementById("searchInput").addEventListener("keypress", event => {

    if (event.key === "Enter") {

        loadProducts(event.target.value);

    }

});


// =====================================================
// PLACE ORDER
// =====================================================

document.getElementById("checkoutButton").addEventListener("click", async () => {

    const orderMessage = document.getElementById("orderMessage");

    // The customer must be logged in.
    if (!authToken) {

        orderMessage.textContent =
            "Please log in before placing an order.";

        orderMessage.style.color = "red";

        return;
    }

    // The cart cannot be empty.
    if (cart.length === 0) {

        orderMessage.textContent = "Your cart is empty.";

        orderMessage.style.color = "red";

        return;
    }

    try {

        // Prepare the order in the format expected by Flask.
        const orderData = {

            items: cart.map(item => ({

                product_id: item.product_id,

                quantity: item.quantity,

                size_id: item.size_id,

                color_id: item.color_id

            }))

        };

        // Send the order to the backend.
        const data = await apiRequest("/api/orders", {

            method: "POST",

            body: JSON.stringify(orderData)

        });

        // Show the success message.
        orderMessage.textContent =
            "Order placed successfully!";

        orderMessage.style.color = "green";

        // Empty the cart after a successful order.
        cart = [];

        updateCart();

        // Refresh products to show updated information.
        await loadProducts();

    } catch (error) {

        orderMessage.textContent = error.message;

        orderMessage.style.color = "red";

    }

});


// =====================================================
// INITIALIZE THE APPLICATION
// =====================================================

// Load categories and products when the page opens.
async function initializeApp() {

    await loadCategories();

    await loadProducts();

    updateCart();

}

// Start the application.
initializeApp();
