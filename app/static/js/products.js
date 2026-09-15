document.addEventListener("DOMContentLoaded", () => {

    /* =========================
       IMAGE PREVIEW
    ========================= */

    const imageInput = document.getElementById("productImage");
    const imagePreview = document.getElementById("imagePreview");

    if (imageInput && imagePreview) {

        imageInput.addEventListener("change", () => {

            const file = imageInput.files[0];

            imagePreview.innerHTML = "";

            if (!file) {
                return;
            }

            const allowedTypes = [
                "image/jpeg",
                "image/png",
                "image/webp"
            ];

            if (!allowedTypes.includes(file.type)) {

                alert("Only JPG, PNG and WEBP images are allowed.");

                imageInput.value = "";

                return;
            }

            const image = document.createElement("img");

            image.src = URL.createObjectURL(file);

            image.alt = "Product preview";

            imagePreview.appendChild(image);
        });
    }


    /* =========================
       CREATE PRODUCT
    ========================= */

    const productForm =
    document.getElementById("productForm");


/* =========================
   DELETE PRODUCT
========================= */

document.querySelectorAll(
    ".admin-delete-btn"
).forEach(button => {

    button.addEventListener(
        "click",
        async () => {

            const productId =
                button.dataset.productId;

            if (!productId) {
                alert("Product ID not found.");
                return;
            }

            if (!confirm(
                "Are you sure you want to delete this product?"
            )) {
                return;
            }

            try {

                button.disabled = true;

                const response =
                    await fetch(
                        `/products/${productId}`,
                        {
                            method: "DELETE"
                        }
                    );

                const text =
                    await response.text();

                let result = {};

                try {
                    result = text
                        ? JSON.parse(text)
                        : {};
                } catch {
                    result = {};
                }

                if (!response.ok) {

                    throw new Error(
                        result.detail ||
                        "Failed to delete product."
                    );

                }

                alert(
                    result.message ||
                    "Product deleted successfully!"
                );

                window.location.reload();

            } catch (error) {

                console.error(
                    "Delete product error:",
                    error
                );

                alert(
                    error.message ||
                    "Failed to delete product."
                );

                button.disabled = false;
            }
        }
    );

});


if (!productForm) {
    return;
}

    const readResponse = async (response) => {
        const responseText = await response.text();

        try {
            return responseText
                ? JSON.parse(responseText)
                : {};
        } catch {
            return {
                detail: response.ok
                    ? "The server returned an invalid response."
                    : `Request failed (${response.status}): ${
                        responseText || response.statusText
                    }`
            };
        }
    };

    productForm.addEventListener("submit", async (event) => {

        event.preventDefault();

        const message =
            document.getElementById("productFormMessage");

        const submitButton = productForm.querySelector(
            'button[type="submit"]'
        );

        /* =========================
           GET SELECTED CATEGORIES
        ========================= */

        const categorySelect =
            document.getElementById("productCategories");

        const categoryIds = Array.from(
            categorySelect.selectedOptions
        ).map(option => Number(option.value));

        // Keep category updates functional if the optional status control is
        // not present in a rendered edit form.
        const activeStatus = document.getElementById(
            "editProductActive"
        );

        if (categoryIds.length === 0) {

            message.textContent =
                "Please select at least one category.";

            return;
        }

        const data = {

            name:
                document.getElementById("productName").value.trim(),

            slug:
                document.getElementById("productSlug").value.trim(),

            description:
                document.getElementById("productDescription").value.trim()
                || null,

            price:
                Number(
                    document.getElementById("productPrice").value
                ),

            discount_price:
                document.getElementById("productDiscountPrice").value
                    ? Number(
                        document.getElementById(
                            "productDiscountPrice"
                        ).value
                    )
                    : null,

            stock:
                Number(
                    document.getElementById("productStock").value
                ),

            material:
                document.getElementById("productMaterial").value.trim()
                || null,

            color:
                document.getElementById("productColor").value.trim()
                || null,

            category_ids:
                categoryIds
        };


        try {

            message.textContent =
                "Creating product...";

            if (submitButton) {
                submitButton.disabled = true;
            }


            /* =========================
               CREATE PRODUCT
            ========================= */

            const response = await fetch("/products/", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(data)

            });


            const result = await readResponse(response);


            if (!response.ok) {

                throw new Error(
                    result.detail || "Failed to create product"
                );

            }


            const productId = result.id;


            /* =========================
               UPLOAD IMAGE
            ========================= */

            const file =
                imageInput?.files[0];


            let imageUploadError = null;


            if (file) {

                try {

                    message.textContent =
                        "Uploading product image...";


                    const formData = new FormData();

                    // Include the original filename when uploading
                    formData.append("image", file, file.name);


                    const imageResponse =
                        await fetch(
                            `/products/${productId}/images`,
                            {
                                method: "POST",
                                body: formData
                            }
                        );


                    const imageResult =
                        await readResponse(imageResponse);


                    if (!imageResponse.ok) {

                        throw new Error(
                            imageResult.detail ||
                            "Image upload failed"
                        );

                    }

                } catch (error) {

                    imageUploadError = error;

                }

            }


            if (imageUploadError) {

                message.textContent =
                    "Product created successfully, but its image could not " +
                    "be uploaded. Redirecting to the product editor...";

                message.classList.add("form-warning-message");

                await new Promise(resolve => {
                    window.setTimeout(resolve, 2000);
                });

                window.location.href =
                    `/admin/products/${productId}/edit`;

                return;

            }


            /* =========================
               SUCCESS
            ========================= */

            message.textContent =
                "Product created successfully! Redirecting to products...";

            message.classList.add("form-success-message");

            await new Promise(resolve => {
                window.setTimeout(resolve, 1500);
            });


            window.location.href =
                "/admin/products";


        } catch (error) {

            console.error(error);

            message.textContent =
                error.message;

            message.classList.remove("form-success-message");

            if (submitButton) {
                submitButton.disabled = false;
            }

        }

    });

});


async function parseApiResponse(response) {
    const text = await response.text();
    try {
        return text ? JSON.parse(text) : {};
    } catch {
        return {
            detail: response.ok
                ? "The server returned an invalid response."
                : `Request failed (${response.status}).`
        };
    }
}

/* =========================
   EDIT PRODUCT
========================= */

const editProductForm =
    document.getElementById("editProductForm");

const editActiveStatus = document.getElementById("editProductActive");

if (editProductForm) {

    editProductForm.addEventListener("submit", async (event) => {

        event.preventDefault();


        const productId =
            document.getElementById("editProductId").value;


        /* =========================
           GET SELECTED CATEGORIES
        ========================= */

        const categorySelect =
            document.getElementById("editProductCategories");

        const categoryIds = Array.from(
            categorySelect.selectedOptions
        ).map(option => Number(option.value));


        if (categoryIds.length === 0) {

            document.getElementById(
                "editProductMessage"
            ).textContent =
                "Please select at least one category.";

            return;
        }


        const data = {

            name:
                document.getElementById(
                    "editProductName"
                ).value.trim(),

            slug:
                document.getElementById(
                    "editProductSlug"
                ).value.trim(),

            description:
                document.getElementById(
                    "editProductDescription"
                ).value.trim()
                || null,

            price:
                Number(
                    document.getElementById(
                        "editProductPrice"
                    ).value
                ),

            discount_price:
                document.getElementById(
                    "editProductDiscount"
                ).value
                    ? Number(
                        document.getElementById(
                            "editProductDiscount"
                        ).value
                    )
                    : null,

            stock:
                Number(
                    document.getElementById(
                        "editProductStock"
                    ).value
                ),

            material:
                document.getElementById(
                    "editProductMaterial"
                ).value.trim()
                || null,

            color:
                document.getElementById(
                    "editProductColor"
                ).value.trim()
                || null,

            category_ids:
                categoryIds,

            is_active:
                editActiveStatus
                    ? editActiveStatus.value === "true"
                    : undefined

        };


        try {

            const response = await fetch(
                `/products/${productId}`,
                {
                    method: "PUT",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify(data)
                }
            );


            const result =
                await parseApiResponse(response);


            if (!response.ok) {

                throw new Error(
                    result.detail ||
                    "Failed to update product"
                );

            }


            alert(
                "Product updated successfully!"
            );


            window.location.href =
                "/admin/products";


        } catch (error) {

            console.error(error);

            document.getElementById(
                "editProductMessage"
            ).textContent =
                error.message;

        }

    });

}


/* =========================
   UPLOAD PRODUCT IMAGE
========================= */

const uploadImageButton =
    document.getElementById("uploadProductImage");

if (uploadImageButton) {

    uploadImageButton.addEventListener(
        "click",
        async () => {

            const productId =
                document.getElementById(
                    "editProductId"
                ).value;


            const input =
                document.getElementById(
                    "editProductImage"
                );


            const file =
                input.files[0];


            if (!file) {

                alert(
                    "Please select an image."
                );

                return;
            }


            const formData = new FormData();

            // Include the original filename when uploading
            formData.append("image", file, file.name);


            const response =
                await fetch(
                    `/products/${productId}/images`,
                    {
                        method: "POST",
                        body: formData
                    }
                );


            const result =
                await parseApiResponse(response);


            if (!response.ok) {

                alert(
                    result.detail ||
                    "Upload failed."
                );

                return;
            }


            alert(
                "Image uploaded successfully!"
            );


            window.location.reload();

        }
    );

}


/* =========================
   DELETE PRODUCT IMAGE
========================= */

document.querySelectorAll(
    ".delete-image-btn"
).forEach(button => {

    button.addEventListener(
        "click",
        async () => {

            if (!confirm(
                "Delete this image?"
            )) {
                return;
            }


            const productId =
                button.dataset.productId;


            const imageId =
                button.dataset.imageId;


            const response =
                await fetch(
                    `/products/${productId}/images/${imageId}`,
                    {
                        method: "DELETE"
                    }
                );


            const result =
                await parseApiResponse(response);


            if (!response.ok) {

                alert(
                    result.detail ||
                    "Delete failed."
                );

                return;
            }


            window.location.reload();

        }
    );

});


/* =========================
   SET PRIMARY IMAGE
========================= */

document.querySelectorAll(
    ".set-primary-btn"
).forEach(button => {

    button.addEventListener(
        "click",
        async () => {

            const productId =
                button.dataset.productId;


            const imageId =
                button.dataset.imageId;


            const response =
                await fetch(
                    `/products/${productId}/images/${imageId}/primary`,
                    {
                        method: "PUT"
                    }
                );


            const result =
                await parseApiResponse(response);


            if (!response.ok) {

                alert(
                    result.detail ||
                    "Failed."
                );

                return;
            }


            window.location.reload();

        }
    );

});
