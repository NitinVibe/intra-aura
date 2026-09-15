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
