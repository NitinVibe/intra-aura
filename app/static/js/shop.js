let currentUserId = "guest";


async function loadCurrentUser() {

    try {

        const response =
            await fetch("/account/current-user");

        const data =
            await response.json();

        if (data.logged_in) {

            currentUserId =
                String(data.id);

        } else {

            currentUserId = "guest";

        }

    } catch (error) {

        console.error(
            "Could not load current user:",
            error
        );

        currentUserId = "guest";
    }
}


/* =========================================
   STORAGE KEYS
========================================= */

function getCartKey() {

    return `intraAuraCart_${currentUserId}`;

}


function getWishlistKey() {

    return `intraAuraWishlist_${currentUserId}`;

}


/* =========================================
   INITIALIZE
========================================= */

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        await loadCurrentUser();

        setupCartButtons();
        setupWishlistButtons();

        updateCartCount();
        updateWishlistCount();

        updateWishlistButtonStates();

        renderCart();
        renderWishlist();

    }
);
/* =========================================
   CART
========================================= */

function getCart() {

    const cart =
        localStorage.getItem(
            getCartKey()
        );

    if (!cart) {
        return [];
    }

    try {

        return JSON.parse(cart);

    } catch (error) {

        console.error(
            "Invalid cart data:",
            error
        );

        return [];
    }
}


function saveCart(cart) {

    localStorage.setItem(
        getCartKey(),
        JSON.stringify(cart)
    );

}


/* =========================================
   ADD TO CART
========================================= */
/* =========================================
   ADD TO CART
========================================= */

function addToCart(product) {

    const cart = getCart();

    const existingProduct = cart.find(
        item => item.id === product.id
    );


    if (existingProduct) {

        existingProduct.quantity += 1;

    } else {

        cart.push({

            id: product.id,

            name: product.name,

            price: Number(product.price),

            image: product.image || "",

            quantity: 1

        });

    }


    saveCart(cart);

    updateCartCount();

    renderCart();

}

/* =========================================
   CART BUTTONS
========================================= */
/* =========================================
   CART BUTTONS
========================================= */

function setupCartButtons() {

    const buttons = document.querySelectorAll(
        ".product-add-cart-btn, .product-cart-btn, .detail-add-cart-btn"
    );


    buttons.forEach(button => {

        /* Prevent duplicate click listeners */

        if (button.dataset.cartReady === "true") {
            return;
        }

        button.dataset.cartReady = "true";


        button.addEventListener("click", function () {

            const productId =
                Number(button.dataset.productId);

            const productName =
                button.dataset.productName || "";

            const productPrice =
                Number(button.dataset.productPrice || 0);

            const productImage =
                button.dataset.productImage || "";


            if (!productId) {

                console.error(
                    "Cart: Product ID missing"
                );

                return;
            }


            addToCart({

                id: productId,

                name: productName,

                price: productPrice,

                image: productImage

            });

        });

    });

}

/* =========================================
   CART COUNT
========================================= */

function updateCartCount() {

    const cart = getCart();


    const count = cart.reduce(
        (total, item) => {
            return total + Number(item.quantity || 0);
        },
        0
    );


    document.querySelectorAll(
        ".cart-count"
    ).forEach(element => {

        element.textContent = count;

        element.style.display =
            count > 0 ? "flex" : "none";

    });

}


/* =========================================
   WISHLIST
========================================= */

function getWishlist() {

    const wishlist =
        localStorage.getItem(
            getWishlistKey()
        );

    if (!wishlist) {
        return [];
    }

    try {

        return JSON.parse(wishlist);

    } catch (error) {

        console.error(
            "Invalid wishlist data:",
            error
        );

        return [];
    }
}


function saveWishlist(wishlist) {

    localStorage.setItem(
        getWishlistKey(),
        JSON.stringify(wishlist)
    );

}


/* =========================================
   TOGGLE WISHLIST
========================================= */

function toggleWishlist(product) {

    const wishlist = getWishlist();


    const existingIndex =
        wishlist.findIndex(
            item => item.id === product.id
        );


    if (existingIndex !== -1) {

        /*
         * Product already exists,
         * so remove it.
         */

        wishlist.splice(
            existingIndex,
            1
        );

    } else {

        /*
         * Product doesn't exist,
         * so add it.
         */

        wishlist.push({

            id: product.id,

            name: product.name,

            price: Number(product.price),

            image: product.image || ""

        });

    }


    saveWishlist(wishlist);

    updateWishlistCount();

    updateWishlistButtonStates();

}


/* =========================================
   WISHLIST BUTTONS
========================================= */
/* =========================================
   WISHLIST BUTTONS
========================================= */

function setupWishlistButtons() {

    document
        .querySelectorAll(
            ".product-wishlist-btn, .detail-wishlist-btn"
        )
        .forEach(button => {

            /* Prevent duplicate listeners */

            if (button.dataset.wishlistReady === "true") {
                return;
            }

            button.dataset.wishlistReady = "true";


            button.addEventListener("click", function () {

                const productId =
                    Number(button.dataset.productId);

                const productName =
                    button.dataset.productName || "";

                const productPrice =
                    Number(button.dataset.productPrice || 0);

                const productImage =
                    button.dataset.productImage || "";


                if (!productId) {

                    console.error(
                        "Wishlist: Product ID missing"
                    );

                    return;
                }


                toggleWishlist({

                    id: productId,

                    name: productName,

                    price: productPrice,

                    image: productImage

                });

            });

        });

}
/* =========================================
   WISHLIST COUNT
========================================= */

function updateWishlistCount() {

    const wishlist =
        getWishlist();


    const count =
        wishlist.length;


    document.querySelectorAll(
        ".wishlist-count"
    ).forEach(element => {

        element.textContent = count;

        element.style.display =
            count > 0 ? "flex" : "none";

    });

}


/* =========================================
   UPDATE HEART ICONS
========================================= */

function updateWishlistButtonStates() {

    const wishlist =
        getWishlist();


    document.querySelectorAll(
        ".product-wishlist-btn, .detail-wishlist-btn"
    ).forEach(button => {

        const productId =
            Number(
                button.dataset.productId
            );


        const exists =
            wishlist.some(
                item => item.id === productId
            );


        if (exists) {

            button.classList.add("active");

            button.textContent = "♥";

        } else {

            button.classList.remove("active");

            button.textContent = "♡";

        }

    });

}

/* =========================================
   WISHLIST PAGE
========================================= */

function renderWishlist() {

    const container =
        document.getElementById("wishlistItems");

    if (!container) {
        return;
    }


    const wishlist = getWishlist();


    /* EMPTY WISHLIST */

    if (wishlist.length === 0) {

        container.innerHTML = `
            <div class="wishlist-empty">

                <h2>
                    Your wishlist is empty.
                </h2>

                <p>
                    Save pieces you love and
                    come back to them later.
                </p>

                <a href="/products">
                    Explore Products
                </a>

            </div>
        `;

        return;
    }


    /* RENDER PRODUCTS */

    container.innerHTML = wishlist.map(item => {

        return `

            <article class="wishlist-card">

                <div class="wishlist-card-image">

                    ${
                        item.image
                        ?
                        `
                        <img
                            src="${item.image}"
                            alt="${escapeHtml(item.name)}"
                        >
                        `
                        :
                        `
                        <div class="wishlist-card-placeholder">
                            INTRA AURA
                        </div>
                        `
                    }

                </div>


                <div class="wishlist-card-info">

                    <p class="wishlist-card-label">
                        SAVED PIECE
                    </p>

                    <h3>
                        ${escapeHtml(item.name)}
                    </h3>

                    <strong class="wishlist-card-price">
                        ₹${formatPrice(item.price)}
                    </strong>


                    <div class="wishlist-card-actions">

                        <button
                            type="button"
                            class="wishlist-move-cart-btn"
                            onclick="moveWishlistToCart(${item.id})"
                        >
                            Move to Cart
                            <span>→</span>
                        </button>


                        <button
                            type="button"
                            class="wishlist-remove-btn"
                            onclick="removeFromWishlist(${item.id})"
                        >
                            Remove
                        </button>

                    </div>

                </div>

            </article>

        `;

    }).join("");

}

/* =========================================
   REMOVE FROM WISHLIST
========================================= */

function removeFromWishlist(productId) {

    const wishlist = getWishlist();

    const updatedWishlist =
        wishlist.filter(
            item => item.id !== productId
        );


    saveWishlist(updatedWishlist);

    updateWishlistCount();

    updateWishlistButtonStates();

    renderWishlist();

}


/* =========================================
   MOVE WISHLIST → CART
========================================= */

function moveWishlistToCart(productId) {

    const wishlist = getWishlist();

    const product =
        wishlist.find(
            item => item.id === productId
        );


    if (!product) {
        return;
    }


    /* Add product to cart */

    addToCart({
        id: product.id,
        name: product.name,
        price: product.price,
        image: product.image
    });


    /* Remove from wishlist */

    const updatedWishlist =
        wishlist.filter(
            item => item.id !== productId
        );


    saveWishlist(updatedWishlist);


    /* Update UI */

    updateWishlistCount();

    updateWishlistButtonStates();

    renderWishlist();

}
/* =========================================
   GLOBAL FUNCTIONS
========================================= */

window.addToCart = addToCart;

window.toggleWishlist = toggleWishlist;

window.updateCartCount = updateCartCount;

window.updateWishlistCount = updateWishlistCount;

window.removeFromWishlist =
    removeFromWishlist;

window.moveWishlistToCart =
    moveWishlistToCart;

window.renderWishlist =
    renderWishlist;

/* =========================================
   CART PAGE
========================================= */

function renderCart() {

    const cartItems =
        document.getElementById("cartItems");

    const emptyCart =
        document.getElementById("emptyCart");

    const cartSummary =
        document.getElementById("cartSummary");


    // Not on cart page
    if (!cartItems) {
        return;
    }


    const cart = getCart();


    if (cart.length === 0) {

        cartItems.innerHTML = "";

        emptyCart.style.display = "flex";

        cartSummary.style.display = "none";

        return;
    }


    emptyCart.style.display = "none";

    cartSummary.style.display = "block";


    cartItems.innerHTML = cart.map(item => {

        const subtotal =
            Number(item.price) *
            Number(item.quantity);


        return `

            <article class="cart-item">

                <div class="cart-item-image">

                    ${
                        item.image
                        ?
                        `<img
                            src="${item.image}"
                            alt="${escapeHtml(item.name)}"
                        >`
                        :
                        `<div class="cart-item-placeholder">
                            INTRA AURA
                        </div>`
                    }

                </div>


                <div class="cart-item-info">

                    <p class="cart-item-label">
                        SELECTED PIECE
                    </p>

                    <h3>
                        ${escapeHtml(item.name)}
                    </h3>


                    <p class="cart-item-price">
                        ₹${formatPrice(item.price)}
                    </p>


                    <div class="cart-item-actions">

                        <div class="quantity-control">

                            <button
                                type="button"
                                onclick="changeCartQuantity(${item.id}, -1)"
                            >
                                −
                            </button>

                            <span>
                                ${item.quantity}
                            </span>

                            <button
                                type="button"
                                onclick="changeCartQuantity(${item.id}, 1)"
                            >
                                +
                            </button>

                        </div>


                        <button
                            type="button"
                            class="cart-remove-btn"
                            onclick="removeFromCart(${item.id})"
                        >
                            Remove
                        </button>

                    </div>

                </div>


                <div class="cart-item-subtotal">

                    <span>
                        Subtotal
                    </span>

                    <strong>
                        ₹${formatPrice(subtotal)}
                    </strong>

                </div>

            </article>

        `;

    }).join("");


    updateCartSummary();

}


/* =========================================
   CHANGE QUANTITY
========================================= */

function changeCartQuantity(productId, change) {

    const cart = getCart();


    const product =
        cart.find(item => item.id === productId);


    if (!product) {
        return;
    }


    product.quantity += change;


    if (product.quantity <= 0) {

        const index =
            cart.findIndex(
                item => item.id === productId
            );

        cart.splice(index, 1);

    }


    saveCart(cart);

    updateCartCount();

    renderCart();

}


/* =========================================
   REMOVE FROM CART
========================================= */

function removeFromCart(productId) {

    const cart = getCart();


    const updatedCart =
        cart.filter(
            item => item.id !== productId
        );


    saveCart(updatedCart);

    updateCartCount();

    renderCart();

}


/* =========================================
   CART SUMMARY
========================================= */

function updateCartSummary() {

    const cart = getCart();


    const itemCount =
        cart.reduce(
            (total, item) =>
                total + Number(item.quantity),
            0
        );


    const total =
        cart.reduce(
            (total, item) =>
                total +
                (
                    Number(item.price) *
                    Number(item.quantity)
                ),
            0
        );


    const countElement =
        document.getElementById("cartItemCount");

    const subtotalElement =
        document.getElementById("cartSubtotal");

    const totalElement =
        document.getElementById("cartTotal");


    if (countElement) {

        countElement.textContent =
            itemCount;

    }


    if (subtotalElement) {

        subtotalElement.textContent =
            `₹${formatPrice(total)}`;

    }


    if (totalElement) {

        totalElement.textContent =
            `₹${formatPrice(total)}`;

    }

}


/* =========================================
   PRICE FORMAT
========================================= */

function formatPrice(price) {

    return Number(price).toLocaleString(
        "en-IN",
        {
            maximumFractionDigits: 0
        }
    );

}


/* =========================================
   ESCAPE HTML
========================================= */

function escapeHtml(value) {

    const div =
        document.createElement("div");

    div.textContent = value;

    return div.innerHTML;

}


/* =========================================
   GLOBAL CART FUNCTIONS
========================================= */

window.changeCartQuantity =
    changeCartQuantity;

window.removeFromCart =
    removeFromCart;

window.renderCart =
    renderCart;



/* =========================================
   CART → CONTACT
========================================= */

function connectCart() {

    const cart = getCart();

    if (cart.length === 0) {
        alert("Your cart is empty.");
        return;
    }

    sessionStorage.setItem(
        "intraAuraEnquiryCart",
        JSON.stringify(cart)
    );

    window.location.href = "/contact?from_cart=1";
}


document.addEventListener("DOMContentLoaded", () => {

    const connectButton =
        document.getElementById("cartConnectBtn");

    if (connectButton) {

        connectButton.addEventListener(
            "click",
            connectCart
        );

    }

});