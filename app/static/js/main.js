const menuToggle = document.getElementById("menuToggle");
const mobileMenu = document.getElementById("mobileMenu");

if (menuToggle && mobileMenu) {

    menuToggle.addEventListener("click", () => {
        mobileMenu.classList.toggle("active");
    });

}
function changeProductImage(imageUrl, thumbnail) {

    const mainImage = document.getElementById("mainProductImage");

    if (!mainImage) {
        return;
    }

    mainImage.src = imageUrl;

    document
        .querySelectorAll(".product-thumbnail")
        .forEach(item => {
            item.classList.remove("active");
        });

    thumbnail.classList.add("active");
}

/* =========================================
   CART ENQUIRY SUBMISSION
========================================= */

const enquiryForm = document.getElementById("enquiryForm");

if (enquiryForm) {

    enquiryForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const formMessage =
            document.getElementById("formMessage");

        const cartDataInput =
            document.getElementById("cartData");

        const cartTotalInput =
            document.getElementById("cartTotal");


        /* -----------------------------
           GET CART
        ----------------------------- */

        const cart = JSON.parse(
            sessionStorage.getItem(
                "intraAuraEnquiryCart"
            ) || "[]"
        );


        /* -----------------------------
           FORM DATA
        ----------------------------- */

        const data = {

            name:
                document.getElementById("name").value.trim(),

            email:
                document.getElementById("email").value.trim(),

            phone:
                document.getElementById("phone").value.trim(),

            message:
                document.getElementById("message").value.trim(),

            cart_data:
                JSON.stringify(cart),

            cart_total:
                cartTotalInput
                    ? Number(cartTotalInput.value || 0)
                    : 0

        };


        /* -----------------------------
           VALIDATION
        ----------------------------- */

        if (!data.name ||
            !data.email ||
            !data.phone) {

            formMessage.textContent =
                "Please fill in all required fields.";

            return;
        }


        


        /* -----------------------------
           SUBMIT
        ----------------------------- */

        try {

            formMessage.textContent =
                "Sending enquiry...";


            const response = await fetch(
                "/enquiries/",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify(data)
                }
            );


            const result =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    result.detail ||
                    "Failed to submit enquiry"
                );

            }


            /* -----------------------------
               SUCCESS
            ----------------------------- */

            formMessage.textContent =
                "Enquiry submitted successfully!";


            /* Clear enquiry cart */

            sessionStorage.removeItem(
                "intraAuraEnquiryCart"
            );


            /* Clear form */

            enquiryForm.reset();


        } catch (error) {

            console.error(error);

            formMessage.textContent =
                error.message ||
                "Unable to submit enquiry. Please try again.";

        }

    });

}

document.addEventListener("DOMContentLoaded", function () {

    const slides = document.querySelectorAll(".home-hero-slide");
    const dots = document.querySelectorAll(".hero-dot");

    if (!slides.length) return;

    let currentSlide = 0;
    let sliderTimer;


    function showSlide(index) {

        slides.forEach((slide, i) => {
            slide.classList.toggle("active", i === index);
        });

        dots.forEach((dot, i) => {
            dot.classList.toggle("active", i === index);
        });

        currentSlide = index;
    }


    function nextSlide() {

        const next =
            (currentSlide + 1) % slides.length;

        showSlide(next);
    }


    function startSlider() {

        clearInterval(sliderTimer);

        sliderTimer = setInterval(
            nextSlide,
            5000
        );
    }


    dots.forEach((dot, index) => {

        dot.addEventListener("click", function () {

            showSlide(index);

            startSlider();

        });

    });


    showSlide(0);

    startSlider();

});

/* =========================================
   FEATURED PRODUCTS
   SMOOTH INFINITE LOOP
========================================= */

document.addEventListener("DOMContentLoaded", function () {

    const track =
        document.getElementById("featuredTrack");

    const carousel =
        document.querySelector(".featured-carousel");


    if (!track || !carousel) {
        return;
    }


    const originalCards =
        Array.from(
            track.querySelectorAll(".featured-card")
        );


    if (originalCards.length <= 1) {
        return;
    }


    /* =========================================
       CREATE MULTIPLE COPIES
    ========================================= */

    const originalHTML =
        track.innerHTML;


    track.innerHTML =
        originalHTML +
        originalHTML +
        originalHTML;


    const cards =
        Array.from(
            track.querySelectorAll(".featured-card")
        );


    /*
     * Start from the middle copy.
     */

    let currentIndex =
        originalCards.length;


    /* =========================================
       CARD STEP
    ========================================= */

    function getStep() {

        const card =
            cards[0];

        const cardWidth =
            card.getBoundingClientRect().width;

        const gap =
            parseFloat(
                getComputedStyle(track).gap
            ) || 0;

        return cardWidth + gap;

    }


    /* =========================================
       MOVE
    ========================================= */

    function moveCarousel(animate = true) {

        const step =
            getStep();


        track.style.transition =
            animate
                ? "transform 0.9s cubic-bezier(0.22, 1, 0.36, 1)"
                : "none";


        track.style.transform =
            `translateX(-${currentIndex * step}px)`;

    }


    /* =========================================
       INITIAL POSITION
    ========================================= */

    moveCarousel(false);


    /* =========================================
       NEXT PRODUCT
    ========================================= */

    function nextSlide() {

        currentIndex++;

        moveCarousel(true);

    }


    /* =========================================
       EVERY 3 SECONDS
    ========================================= */

    setInterval(function () {

        nextSlide();

    }, 3000);


    /* =========================================
       SEAMLESS LOOP
    ========================================= */

    track.addEventListener(
        "transitionend",
        function () {

            /*
             * We have moved into the third copy.
             * Jump back to the identical position
             * in the middle copy.
             */

            if (
                currentIndex >=
                originalCards.length * 2
            ) {

                currentIndex -=
                    originalCards.length;

                moveCarousel(false);

            }

        }
    );


    /* =========================================
       RESPONSIVE
    ========================================= */

    window.addEventListener(
        "resize",
        function () {

            moveCarousel(false);

        }
    );

});

/* =========================================
   CATEGORY CAROUSEL
   SMOOTH LEFT → RIGHT
========================================= */

document.addEventListener("DOMContentLoaded", function () {

    const track =
        document.querySelector(".categories-track");

    const carousel =
        document.querySelector(".categories-carousel");


    if (!track || !carousel) {
        return;
    }


    const originalCards =
        Array.from(
            track.querySelectorAll(".category-card")
        );


    if (originalCards.length <= 1) {
        return;
    }


    /* =========================================
       CLONE CARDS
    ========================================= */

    originalCards.forEach(function (card) {

        const clone =
            card.cloneNode(true);

        track.appendChild(clone);

    });


    const cards =
        Array.from(
            track.querySelectorAll(".category-card")
        );


    let currentIndex =
        originalCards.length;


    /* =========================================
       GET CARD STEP
    ========================================= */

    function getStep() {

        const card =
            cards[0];

        const width =
            card.getBoundingClientRect().width;

        const gap =
            parseFloat(
                getComputedStyle(track).gap
            ) || 0;

        return width + gap;

    }


    /* =========================================
       POSITION
    ========================================= */

    function updatePosition(animate = true) {

        const step =
            getStep();


        track.style.transition =
            animate
                ? "transform 0.8s cubic-bezier(0.22, 1, 0.36, 1)"
                : "none";


        track.style.transform =
            `translate3d(-${currentIndex * step}px, 0, 0)`;

    }


    /* =========================================
       START
    ========================================= */

    updatePosition(false);


    /* =========================================
       MOVE LEFT → RIGHT
    ========================================= */

    function previousSlide() {

        currentIndex--;

        updatePosition(true);

    }


    /* =========================================
       EVERY 3 SECONDS
    ========================================= */

    setInterval(function () {

        previousSlide();

    }, 3000);


    /* =========================================
       SEAMLESS RESET
    ========================================= */

    track.addEventListener(
        "transitionend",
        function () {

            if (
                currentIndex <= 0
            ) {

                currentIndex =
                    originalCards.length;

                updatePosition(false);

            }

        }
    );


    /* =========================================
       RESPONSIVE
    ========================================= */

    window.addEventListener(
        "resize",
        function () {

            updatePosition(false);

        }
    );

});