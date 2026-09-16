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

    // Show first letter of logged-in user's name
    const initial =
        data.name
            ? data.name.trim().charAt(0).toUpperCase()
            : "";

    const avatar =
        document.getElementById("profileAvatar");

    const avatarLarge =
        document.getElementById("profileAvatarLarge");

    const welcome =
        document.getElementById("profileWelcome");

    const email =
        document.getElementById("profileEmail");

    if (avatar) {
        avatar.textContent = initial;
    }

    if (avatarLarge) {
        avatarLarge.textContent = initial;
    }

    if (welcome) {
        welcome.textContent = data.name;
    }

    if (email) {
        email.textContent = data.email;
    }

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
                            ${(window.SITE_NAME || "").toUpperCase()}
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
                            ${(window.SITE_NAME || "").toUpperCase()}
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

    <button
        type="button"
        class="cart-buy-item-btn"
        onclick="buyCartItem(${item.id})"
    >
        Buy Now
        <span>→</span>
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



/* =========================================
   CART → BUY NOW / CHECKOUT
========================================= */

let checkoutContext = null;


function getCheckoutCartItems() {
    return getCart().map(item => ({
        id: Number(item.id),
        quantity: Number(item.quantity)
    }));
}


function checkoutItemsAreValid(items) {
    return Array.isArray(items)
        && items.length > 0
        && items.every(
            item =>
                Number(item.id) > 0
                && Number(item.quantity) > 0
        );
}


function setCheckoutContext(items, source) {
    checkoutContext = {
        items: items.map(item => ({
            id: Number(item.id),
            quantity: Number(item.quantity)
        })),
        source: source || "product"
    };
}


function buyCartItem(productId) {

    const cart = getCart();

    const item = cart.find(
        item => item.id === productId
    );

    if (!item) {
        alert("Product not found in cart.");
        return;
    }

    startCheckout(
        [{
            id: Number(item.id),
            quantity: Number(item.quantity)
        }],
        "single",
        "/cart"
    );
}


function buyAllCartItems() {

    const cart = getCheckoutCartItems();

    if (!cart.length) {
        alert("Your cart is empty.");
        return;
    }

    startCheckout(
        cart,
        "all",
        "/cart"
    );
}


function startProductCheckout(productId, quantity = 1) {

    const items = [{
        id: Number(productId),
        quantity: Number(quantity)
    }];

    startCheckout(
        items,
        "product",
        `/products/${Number(productId)}?buy_now=1`
    );
}


async function startCheckout(
    items,
    source = "product",
    returnPath = "/cart"
) {

    if (!checkoutItemsAreValid(items)) {
        alert("Unable to start checkout.");
        return;
    }

    setCheckoutContext(items, source);

    const button = document.getElementById("cartBuyAllBtn");

    if (button) {
        button.disabled = true;
    }

    try {

        const response = await fetch(
            "/account/checkout",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    items: checkoutContext.items
                })
            }
        );

        const result = await response.json();

        if (response.status === 401) {

            window.location.href =
                `/account/login?next=${encodeURIComponent(returnPath)}`;

            return;
        }


        if (
            response.status === 409
            && result.detail?.code === "profile_incomplete"
        ) {

            openCheckoutProfileModal(
                result.detail.profile || {}
            );

            if (
                result.detail.field_errors
                && Object.keys(result.detail.field_errors).length
            ) {

                showCheckoutErrors(
                    result.detail.field_errors,
                    "Some saved details need to be corrected."
                );

            }

            return;
        }


        if (response.status === 503) {

            const message =
                result.detail?.message
                || "Online payment is not configured yet.";

            alert(message);
            return;
        }


        if (!response.ok) {

            const detail = result.detail;

            throw new Error(
                typeof detail === "string"
                    ? detail
                    : detail?.message
                    || "Unable to start checkout."
            );

        }


        launchRazorpayCheckout(result.payment);

    } catch (error) {

        console.error(error);

        alert(
            error.message
            || "Unable to start checkout. Please try again."
        );

    } finally {

        if (button) {
            button.disabled = false;
        }

    }
}


/* =========================================
   CHECKOUT PROFILE MODAL
========================================= */

function openCheckoutProfileModal(profile) {

    const modal =
        document.getElementById("checkoutProfileModal");

    if (!modal) {
        alert("Checkout form is unavailable. Please refresh the page.");
        return;
    }

    const fields = {

        name: "checkoutName",
        email: "checkoutEmail",
        phone: "checkoutPhone",
        address: "checkoutAddress",
        area_street: "checkoutArea",
        landmark: "checkoutLandmark",
        city: "checkoutCity",
        state: "checkoutState",
        pincode: "checkoutPincode"

    };


    Object.entries(fields).forEach(
        ([key, id]) => {

            const input =
                document.getElementById(id);

            if (input) {
                input.value =
                    profile[key] || "";
            }

        }
    );


    clearCheckoutErrors();

    modal.classList.add("active");

    modal.setAttribute(
        "aria-hidden",
        "false"
    );

    document.body.classList.add(
        "checkout-modal-open"
    );


    setTimeout(
        () =>
            document
                .getElementById("checkoutName")
                ?.focus(),
        50
    );
}


function closeCheckoutProfileModal() {

    const modal =
        document.getElementById("checkoutProfileModal");

    if (!modal) {
        return;
    }

    modal.classList.remove("active");

    modal.setAttribute(
        "aria-hidden",
        "true"
    );

    document.body.classList.remove(
        "checkout-modal-open"
    );
}


function clearCheckoutErrors() {

    const errors =
        document.getElementById(
            "checkoutFieldErrors"
        );

    const message =
        document.getElementById(
            "checkoutFormMessage"
        );


    if (errors) {
        errors.innerHTML = "";
    }

    if (message) {
        message.textContent = "";
    }


    document
        .querySelectorAll(
            "#checkoutProfileForm .checkout-field.invalid"
        )
        .forEach(
            el =>
                el.classList.remove("invalid")
        );

}


function showCheckoutErrors(
    fieldErrors,
    message
) {

    clearCheckoutErrors();


    const errors =
        document.getElementById(
            "checkoutFieldErrors"
        );

    const formMessage =
        document.getElementById(
            "checkoutFormMessage"
        );


    if (formMessage) {
        formMessage.textContent =
            message
            || "Please correct the highlighted fields.";
    }


    Object.entries(
        fieldErrors || {}
    ).forEach(
        ([field, error]) => {

            const map = {

                name: "checkoutName",
                email: "checkoutEmail",
                phone: "checkoutPhone",
                address: "checkoutAddress",
                area_street: "checkoutArea",
                landmark: "checkoutLandmark",
                city: "checkoutCity",
                state: "checkoutState",
                pincode: "checkoutPincode"

            };


            const input =
                document.getElementById(
                    map[field]
                );


            if (input) {

                input
                    .closest(".checkout-field")
                    ?.classList.add("invalid");

                input.setAttribute(
                    "aria-invalid",
                    "true"
                );

            }


            if (errors) {

                const row =
                    document.createElement("div");

                row.textContent =
                    `${field.replaceAll("_", " ")}: ${error}`;

                errors.appendChild(row);

            }

        }
    );

}


/* =========================================
   SUBMIT PROFILE → CREATE PAYMENT
========================================= */

async function submitCheckoutProfile(event) {

    event.preventDefault();


    const form =
        event.currentTarget;

    const button =
        document.getElementById(
            "checkoutContinueBtn"
        );


    if (
        !checkoutContext
        || !checkoutItemsAreValid(
            checkoutContext.items
        )
    ) {

        closeCheckoutProfileModal();

        alert(
            "Your checkout session has expired. Please try again."
        );

        return;
    }


    clearCheckoutErrors();


    button.disabled = true;

    button.classList.add("loading");


    const arrow =
        button.querySelector("span");

    if (arrow) {
        arrow.textContent = "…";
    }


    const profile =
        Object.fromEntries(
            new FormData(form).entries()
        );


    try {

        const response =
            await fetch(
                "/account/checkout",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        profile,

                        items:
                            checkoutContext.items

                    })

                }
            );


        const result =
            await response.json();


        if (response.status === 401) {

            window.location.href =
                `/account/login?next=${encodeURIComponent(
                    "/cart"
                )}`;

            return;

        }


        if (!response.ok) {

            const detail =
                result.detail || {};


            if (
                detail.code
                === "validation_error"
            ) {

                showCheckoutErrors(
                    detail.field_errors || {},
                    "Please correct the highlighted fields."
                );

                return;

            }


            throw new Error(
                typeof detail === "string"
                    ? detail
                    : detail.message
                    || "Please check your details and try again."
            );

        }


        closeCheckoutProfileModal();

        launchRazorpayCheckout(
            result.payment
        );

    } catch (error) {

        console.error(error);

        const message =
            document.getElementById(
                "checkoutFormMessage"
            );

        if (message) {

            message.textContent =
                error.message
                || "Unable to continue checkout.";

        }

    } finally {

        button.disabled = false;

        button.classList.remove(
            "loading"
        );

        if (arrow) {
            arrow.textContent = "→";
        }

    }

}


/* =========================================
   RAZORPAY CHECKOUT
========================================= */

function launchRazorpayCheckout(payment) {

    if (!payment || !payment.razorpay_order_id) {

        alert(
            "Payment session could not be created."
        );

        return;

    }


    if (typeof Razorpay === "undefined") {

        alert(
            "Razorpay Checkout could not load. Please check your internet connection and try again."
        );

        return;

    }


    const options = {

        key: payment.key_id,

        amount: payment.amount,

        currency: payment.currency || "INR",

        name: payment.brand_name || window.SITE_NAME || "",

        description:
            payment.description
            || `Order #${payment.local_order_id}`,

        order_id:
            payment.razorpay_order_id,


        prefill: {

            name: payment.name || "",

            email: payment.email || "",

            contact: payment.contact || ""

        },


        theme: {
            color: "#b58a4a"
        },


        handler:
            function (response) {

                verifyRazorpayPayment(
                    response,
                    payment.local_order_id
                );

            },


        modal: {

            ondismiss:
                function () {

                    alert(
                        "Payment window closed. Your order is still pending. You can continue payment from My Orders."
                    );

                }

        }

    };


    const razorpay =
        new Razorpay(options);


    razorpay.on(
        "payment.failed",
        function (response) {

            const orderId =
                response?.error?.metadata?.order_id;

            if (orderId) {

                markPaymentFailed(
                    orderId
                );

            } else {

                alert(
                    "Payment failed. Please try again from My Orders."
                );

            }

        }
    );


    razorpay.open();

}


async function verifyRazorpayPayment(
    response,
    localOrderId
) {

    try {

        const result =
            await fetch(
                "/account/payments/verify",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        local_order_id:
                            localOrderId,

                        razorpay_payment_id:
                            response.razorpay_payment_id,

                        razorpay_order_id:
                            response.razorpay_order_id,

                        razorpay_signature:
                            response.razorpay_signature

                    })

                }
            );


        const data =
            await result.json();


        if (!result.ok) {

            const detail =
                data.detail;


            throw new Error(
                typeof detail === "string"
                    ? detail
                    : detail?.message
                    || "Payment verification failed."
            );

        }


        finalizeSuccessfulCheckout(
            Number(localOrderId),
            data.redirect_url
        );


    } catch (error) {

        console.error(error);

        alert(
            error.message
            || "Payment verification failed. Please check My Orders."
        );

        window.location.href =
            `/account/orders/${Number(localOrderId)}`;

    }

}


async function markPaymentFailed(
    razorpayOrderId
) {

    try {

        const response =
            await fetch(
                "/account/payments/failed",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        razorpay_order_id:
                            razorpayOrderId
                    })

                }
            );


        const result =
            await response.json();


        if (
            response.ok
            && result.redirect_url
        ) {

            window.location.href =
                result.redirect_url;

        } else {

            alert(
                "Payment failed. You can try again from My Orders."
            );

        }

    } catch (error) {

        console.error(error);

        alert(
            "Payment failed. Please open My Orders."
        );

    }

}


function finalizeSuccessfulCheckout(
    orderId,
    redirectUrl
) {

    if (
        checkoutContext
        && checkoutContext.source === "all"
    ) {

        saveCart([]);

    }


    if (
        checkoutContext
        && checkoutContext.source === "single"
    ) {

        const ids =
            new Set(
                checkoutContext.items.map(
                    item => Number(item.id)
                )
            );


        saveCart(
            getCart().filter(
                item =>
                    !ids.has(
                        Number(item.id)
                    )
            )
        );

    }


    updateCartCount();
    renderCart();


    window.location.href =
        redirectUrl
        || `/account/orders/${orderId}?payment=success`;

}


/* =========================================
   RESUME PAYMENT FOR EXISTING ORDER
========================================= */

async function resumeOrderPayment(orderId) {

    try {

        const response =
            await fetch(
                `/account/orders/${Number(orderId)}/pay`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    }
                }
            );


        const result =
            await response.json();


        if (response.status === 401) {

            window.location.href =
                `/account/login?next=${encodeURIComponent(
                    `/account/orders/${Number(orderId)}`
                )}`;

            return;
        }


        if (!response.ok) {

            const detail =
                result.detail;

            throw new Error(
                typeof detail === "string"
                    ? detail
                    : detail?.message
                    || "This order cannot be paid right now."
            );

        }


        checkoutContext = {
            items: [],
            source: "resume"
        };

        launchRazorpayCheckout(
            result.payment
        );

    } catch (error) {

        alert(
            error.message
            || "Unable to start payment."
        );

    }

}

/* =========================================
   GLOBAL CHECKOUT FUNCTIONS
========================================= */

window.buyCartItem =
    buyCartItem;

window.buyAllCartItems =
    buyAllCartItems;

window.startCheckout =
    startCheckout;

window.startProductCheckout =
    startProductCheckout;

window.resumeOrderPayment =
    resumeOrderPayment;

window.openCheckoutProfileModal =
    openCheckoutProfileModal;

window.closeCheckoutProfileModal =
    closeCheckoutProfileModal;


/* =========================================
   CHECKOUT EVENTS
========================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const checkoutForm =
            document.getElementById(
                "checkoutProfileForm"
            );

        if (checkoutForm) {

            checkoutForm.addEventListener(
                "submit",
                submitCheckoutProfile
            );

        }


        document
            .getElementById(
                "checkoutModalClose"
            )
            ?.addEventListener(
                "click",
                closeCheckoutProfileModal
            );


        document
            .getElementById(
                "checkoutCancelBtn"
            )
            ?.addEventListener(
                "click",
                closeCheckoutProfileModal
            );


        document
            .querySelector(
                "[data-checkout-close]"
            )
            ?.addEventListener(
                "click",
                closeCheckoutProfileModal
            );


        const connectButton =
            document.getElementById(
                "cartConnectBtn"
            );

        if (connectButton) {

            connectButton.addEventListener(
                "click",
                connectCart
            );

        }


        const buyAllButton =
            document.getElementById(
                "cartBuyAllBtn"
            );

        if (buyAllButton) {

            buyAllButton.addEventListener(
                "click",
                buyAllCartItems
            );

        }


        /* Auto-start a product Buy Now flow after
           login redirects back to the product page. */

        const params =
            new URLSearchParams(
                window.location.search
            );

        if (
            params.get("buy_now") === "1"
        ) {

            const productId =
                window.INTRA_AURA_PRODUCT_ID;

            if (productId) {

                setTimeout(
                    () =>
                        startProductCheckout(
                            Number(productId),
                            1
                        ),
                    200
                );

            }

        }

    }
);
