/* =========================================
   PRICE SETTINGS
   Change these values according to
   your sir's pricing.
========================================= */

const PRICE_CONFIG = {

    bhk: {
        1: 100000,
        2: 200000,
        3: 300000,
        4: 400000,
        5: 500000
    },

    rooms: {
        living_room: 30000,
        kitchen: 50000,
        bedroom: 40000,
        bathroom: 25000,
        dining: 30000
    },

    packages: {
        essentials: 1.00,
        premium: 1.25,
        luxe: 1.50
    }

};

document.addEventListener("DOMContentLoaded", function () {

    let currentStep = 1;
    const totalSteps = 4;


    /* =========================================
       ROOM COUNTS
    ========================================= */

    const rooms = {
        living_room: 1,
        kitchen: 1,
        bedroom: 1,
        bathroom: 1,
        dining: 1
    };


    /* =========================================
       ELEMENTS
    ========================================= */

    const screens =
        document.querySelectorAll(
            ".calculator-screen"
        );

    const progressSteps =
        document.querySelectorAll(
            ".calculator-step"
        );

    const progressLines =
        document.querySelectorAll(
            ".progress-line"
        );

    const pageCount =
        document.getElementById(
            "calculatorPageCount"
        );

    const nextButton =
        document.getElementById(
            "calculatorNext"
        );

    const backButton =
        document.getElementById(
            "calculatorBack"
        );

    /* =========================================
   SUMMARY POPUP
========================================= */

const calculatorModal =
    document.getElementById("calculatorModal");

const calculatorModalClose =
    document.getElementById("calculatorModalClose");

const calculatorModalOverlay =
    document.querySelector(".calculator-modal-overlay");

const summaryBhk =
    document.getElementById("summaryBhk");

const summaryRooms =
    document.getElementById("summaryRooms");

const summaryPackage =
    document.getElementById("summaryPackage");

const summaryPrice =
    document.getElementById("summaryPrice");

const summarySubmit =
    document.getElementById("summarySubmit");

const calculatorSummary =
    document.getElementById("calculatorSummary");

const calculatorSuccess =
    document.getElementById("calculatorSuccess");

const summaryDone =
    document.getElementById("summaryDone");


    /* =========================================
       SHOW STEP
    ========================================= */

    function showStep(step) {

        currentStep = step;


        screens.forEach(function (screen) {

            const screenStep =
                Number(
                    screen.dataset.step
                );

            screen.classList.toggle(
                "active",
                screenStep === step
            );

        });


        /* Progress */

        progressSteps.forEach(function (item) {

            const progress =
                Number(
                    item.dataset.progress
                );

            item.classList.toggle(
                "active",
                progress === step
            );

            item.classList.toggle(
                "completed",
                progress < step
            );

        });


        progressLines.forEach(function (line, index) {

            line.classList.toggle(
                "active",
                index < step - 1
            );

        });


        /* Page number */

        if (pageCount) {

            pageCount.textContent =
                `${step}/${totalSteps}`;

        }


        /* Back button */

        if (backButton) {

            backButton.style.visibility =
                step === 1
                    ? "hidden"
                    : "visible";

        }


        /* Last step */

        if (nextButton) {

            if (step === totalSteps) {

                nextButton.textContent =
                    "GET QUOTE";

            } else {

                nextButton.textContent =
                    "NEXT";

            }

        }

    }


    /* =========================================
       VALIDATE STEP
    ========================================= */

    function validateStep(step) {


        /* STEP 1 */

        if (step === 1) {

            const selected =
                document.querySelector(
                    'input[name="bhk"]:checked'
                );


            if (!selected) {

                alert(
                    "Please select your BHK type."
                );

                return false;

            }

        }


        /* STEP 3 */

        if (step === 3) {

            const selected =
                document.querySelector(
                    'input[name="package"]:checked'
                );


            if (!selected) {

                alert(
                    "Please select a package."
                );

                return false;

            }

        }


        /* STEP 4 */

        if (step === 4) {

            const form =
                document.getElementById(
                    "calculatorForm"
                );


            if (!form.checkValidity()) {

                form.reportValidity();

                return false;

            }

        }


        return true;

    }


    /* =========================================
       NEXT
    ========================================= */

    if (nextButton) {

        nextButton.addEventListener(
            "click",
            function () {

                if (!validateStep(currentStep)) {
                    return;
                }


                if (currentStep < totalSteps) {

                    showStep(
                        currentStep + 1
                    );

                } else {

                    openCalculatorSummary();

                }

            }
        );

    }


    /* =========================================
       BACK
    ========================================= */

    if (backButton) {

        backButton.addEventListener(
            "click",
            function () {

                if (currentStep > 1) {

                    showStep(
                        currentStep - 1
                    );

                }

            }
        );

    }


    /* =========================================
       ROOM PLUS
    ========================================= */

    document
        .querySelectorAll(".room-plus")
        .forEach(function (button) {

            button.addEventListener(
                "click",
                function () {

                    const room =
                        button.dataset.room;


                    rooms[room]++;


                    updateRoomCount(room);

                }
            );

        });


    /* =========================================
       ROOM MINUS
    ========================================= */

    document
        .querySelectorAll(".room-minus")
        .forEach(function (button) {

            button.addEventListener(
                "click",
                function () {

                    const room =
                        button.dataset.room;


                    /*
                     * Minimum quantity = 0
                     */

                    if (rooms[room] > 0) {

                        rooms[room]--;

                    }


                    updateRoomCount(room);

                }
            );

        });


    /* =========================================
       UPDATE ROOM COUNT
    ========================================= */

    function updateRoomCount(room) {

        const element =
            document.getElementById(
                `${room}_count`
            );


        if (element) {

            element.textContent =
                rooms[room];

        }

    }

/* =========================================
   OPEN SUMMARY POPUP
========================================= */

function openCalculatorSummary() {

    const bhk =
        document.querySelector(
            'input[name="bhk"]:checked'
        );

    const packageType =
        document.querySelector(
            'input[name="package"]:checked'
        );

    if (!bhk || !packageType) {
        return;
    }


    /* =========================================
       CALCULATE TOTAL
    ========================================= */

    let total =
        PRICE_CONFIG.bhk[
            Number(bhk.value)
        ] || 0;


    let roomTotal = 0;

    Object.keys(rooms).forEach(function (room) {

        roomTotal +=
            rooms[room] *
            (
                PRICE_CONFIG.rooms[room] || 0
            );

    });

    total += roomTotal;


    const multiplier =
        PRICE_CONFIG.packages[
            packageType.value
        ] || 1;

    total =
        total * multiplier;


    /* =========================================
       BHK
    ========================================= */

    summaryBhk.textContent =
        `${bhk.value} BHK${Number(bhk.value) === 5 ? "+" : ""}`;


    /* =========================================
       ROOMS
    ========================================= */

    const roomNames = {

        living_room: "Living Room",

        kitchen: "Kitchen",

        bedroom: "Bedroom",

        bathroom: "Bathroom",

        dining: "Dining"

    };


    summaryRooms.innerHTML = "";


    Object.keys(rooms).forEach(function (room) {

        if (rooms[room] <= 0) {
            return;
        }


        const row =
            document.createElement("div");

        row.className =
            "summary-room";


        row.innerHTML = `

            <span>
                ${roomNames[room]}
            </span>

            <span>
                × ${rooms[room]}
            </span>

        `;


        summaryRooms.appendChild(row);

    });


    /* =========================================
       PACKAGE
    ========================================= */

    const packageNames = {

        essentials: "Essentials",

        premium: "Premium",

        luxe: "Luxe"

    };


    summaryPackage.textContent =
        packageNames[packageType.value]
        || packageType.value;


    /* =========================================
       PRICE
    ========================================= */

    summaryPrice.textContent =
        `₹${Math.round(total)
            .toLocaleString("en-IN")}`;


    /* =========================================
       RESET SUCCESS STATE
    ========================================= */

    calculatorSummary.style.display =
        "block";

    calculatorSuccess.classList.remove(
        "active"
    );


    /* =========================================
       OPEN
    ========================================= */

    calculatorModal.classList.add(
        "active"
    );

    calculatorModal.setAttribute(
        "aria-hidden",
        "false"
    );

    document.body.style.overflow =
        "hidden";

}
/* =========================================
   SUBMIT ENQUIRY
========================================= */

async function submitCalculator() {

    const bhk =
        document.querySelector(
            'input[name="bhk"]:checked'
        );

    const packageType =
        document.querySelector(
            'input[name="package"]:checked'
        );


    if (!bhk || !packageType) {
        return;
    }


    /* =========================================
       CALCULATE TOTAL
    ========================================= */

    let total =
        PRICE_CONFIG.bhk[
            Number(bhk.value)
        ] || 0;


    let roomTotal = 0;

    Object.keys(rooms).forEach(function (room) {

        roomTotal +=
            rooms[room] *
            (
                PRICE_CONFIG.rooms[room] || 0
            );

    });

    total += roomTotal;


    const multiplier =
        PRICE_CONFIG.packages[
            packageType.value
        ] || 1;

    total =
        total * multiplier;


    /* =========================================
       CUSTOMER DATA
    ========================================= */

    const data = {

        name:
            document
                .getElementById("calculatorName")
                .value
                .trim(),

        email:
            document
                .getElementById("calculatorEmail")
                .value
                .trim(),

        phone:
            document
                .getElementById("calculatorPhone")
                .value
                .trim(),

        city:
            document
                .getElementById("calculatorCity")
                .value
                .trim(),

        whatsapp:
            document.querySelector(
                'input[name="whatsapp"]'
            ).checked,

        bhk:
            Number(bhk.value),

        rooms:
            rooms,

        package:
            packageType.value,

        estimated_price:
            Math.round(total)

    };


    /* =========================================
       BUTTON STATE
    ========================================= */

    summarySubmit.disabled = true;

    summarySubmit.innerHTML =
        `SUBMITTING...`;


    /* =========================================
       SEND TO BACKEND
    ========================================= */

    try {

        const response =
    await fetch(
        "/enquiries/",
        {
            method: "POST",

            credentials: "same-origin",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body:
                JSON.stringify({

                            name:
                                data.name,

                            email:
                                data.email,

                            phone:
                                data.phone,

                            message:
                                "Price Calculator Enquiry",

                            calculator_data:
                                JSON.stringify({

                                    bhk:
                                        data.bhk,

                                    rooms:
                                        data.rooms,

                                    package:
                                        data.package,

                                    city:
                                        data.city,

                                    whatsapp:
                                        data.whatsapp

                                }),

                            estimated_price:
                                data.estimated_price

                        })

                }
            );


        const responseData =
            await response.json();


        if (!response.ok) {

            throw new Error(
                responseData.detail ||
                "Unable to submit enquiry"
            );

        }


        /* =========================================
           SUCCESS
        ========================================= */

        calculatorSummary.style.display =
            "none";

        calculatorSuccess.classList.add(
            "active"
        );


        console.log(
            "Calculator enquiry submitted:",
            responseData
        );


    } catch (error) {

        console.error(
            "Calculator submission error:",
            error
        );


        summarySubmit.disabled = false;

        summarySubmit.innerHTML =
            `
                TRY AGAIN
                <span>→</span>
            `;


        alert(
            "Something went wrong. Please try again."
        );

    }

}
/* =========================================
   CLOSE POPUP
========================================= */

function closeCalculatorModal() {

    calculatorModal.classList.remove(
        "active"
    );

    calculatorModal.setAttribute(
        "aria-hidden",
        "true"
    );

    document.body.style.overflow =
        "";

}


/* CLOSE BUTTON */

if (calculatorModalClose) {

    calculatorModalClose.addEventListener(
        "click",
        closeCalculatorModal
    );

}


/* OVERLAY */

if (calculatorModalOverlay) {

    calculatorModalOverlay.addEventListener(
        "click",
        closeCalculatorModal
    );

}


/* SUBMIT */

if (summarySubmit) {

    summarySubmit.addEventListener(
        "click",
        submitCalculator
    );

}


/* DONE */

if (summaryDone) {

    summaryDone.addEventListener(
        "click",
        closeCalculatorModal
    );

}


/* ESCAPE */

document.addEventListener(
    "keydown",
    function (event) {

        if (
            event.key === "Escape" &&
            calculatorModal.classList.contains(
                "active"
            )
        ) {

            closeCalculatorModal();

        }

    }
);
});