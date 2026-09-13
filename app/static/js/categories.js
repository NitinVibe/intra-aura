// =========================================
// ADD CATEGORY
// =========================================

async function addCategory(event) {

    event.preventDefault();

    const name =
        document.getElementById("name").value.trim();

    const slug =
        document.getElementById("slug").value.trim();

    const description =
        document.getElementById("description").value.trim();


    if (!name || !slug) {
        alert("Category name and slug are required.");
        return;
    }


    try {

        const response = await fetch("/categories/", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                name: name,
                slug: slug,
                description: description || null
            })

        });


        const result = await response.json();


        if (!response.ok) {

            alert(
                result.detail ||
                "Failed to add category."
            );

            return;
        }


        alert("Category added successfully.");

        window.location.reload();


    } catch (error) {

        console.error("Add category error:", error);

        alert(
            "Something went wrong while adding the category."
        );

    }

}


document.addEventListener("DOMContentLoaded", () => {

    const deleteButtons = document.querySelectorAll(".admin-delete-btn");

    deleteButtons.forEach(button => {

        button.addEventListener("click", () => {

            const categoryId = button.dataset.categoryId;

            deleteCategory(categoryId);

        });

    });

});


async function deleteCategory(categoryId) {

    if (!confirm("Are you sure you want to delete this category?")) {
        return;
    }

    try {

        const response = await fetch(`/categories/${categoryId}`, {
            method: "DELETE"
        });

        if (!response.ok) {
            throw new Error("Failed to delete category");
        }

        window.location.reload();

    } catch (error) {

        console.error(error);
        alert("Could not delete category.");

    }

}

document.addEventListener("DOMContentLoaded", () => {

    const modal = document.getElementById("editCategoryModal");
    const editForm = document.getElementById("editCategoryForm");
    const closeButton = document.getElementById("closeEditModal");

    if (!modal || !editForm) {
        console.error("Edit category modal/form not found.");
        return;
    }


    // ================================
    // OPEN EDIT MODAL
    // ================================

    document.addEventListener("click", (event) => {

        const button = event.target.closest(".admin-edit-btn");

        if (!button) {
            return;
        }

        const categoryId = button.dataset.categoryId;
        const name = button.dataset.name;
        const slug = button.dataset.slug;
        const description = button.dataset.description;


        document.getElementById("editCategoryId").value =
            categoryId;

        document.getElementById("editName").value =
            name;

        document.getElementById("editSlug").value =
            slug;

        document.getElementById("editDescription").value =
            description;


        modal.classList.add("open");

        document.body.classList.add("modal-open");
    });


    // ================================
    // CLOSE MODAL
    // ================================

    if (closeButton) {

        closeButton.addEventListener("click", () => {

            modal.classList.remove("open");

            document.body.classList.remove("modal-open");

        });

    }


    // Close when clicking outside modal

    modal.addEventListener("click", (event) => {

        if (event.target === modal) {

            modal.classList.remove("open");

            document.body.classList.remove("modal-open");

        }

    });


    // ================================
    // UPDATE CATEGORY
    // ================================

    editForm.addEventListener("submit", async (event) => {

    event.preventDefault();

    const categoryId =
        document.getElementById("editCategoryId").value;

    const name =
        document.getElementById("editName").value.trim();

    const slug =
        document.getElementById("editSlug").value.trim();

    const description =
        document.getElementById("editDescription").value.trim();

    const imageInput =
        document.getElementById("editImage");


    if (!categoryId) {
        alert("Category ID is missing.");
        return;
    }


    try {

        // ==========================================
        // 1. UPDATE CATEGORY DETAILS
        // ==========================================

        const response = await fetch(
            `/categories/${categoryId}`,
            {
                method: "PUT",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    name: name,
                    slug: slug,
                    description: description || null
                })
            }
        );


        const result = await response.json();


        if (!response.ok) {

            alert(
                result.detail ||
                "Failed to update category."
            );

            return;
        }


        // ==========================================
        // 2. UPLOAD NEW IMAGE IF SELECTED
        // ==========================================

        if (
            imageInput &&
            imageInput.files &&
            imageInput.files.length > 0
        ) {

            const formData = new FormData();

            formData.append(
                "image",
                imageInput.files[0]
            );


            const imageResponse = await fetch(
                `/categories/${categoryId}/image`,
                {
                    method: "POST",
                    body: formData
                }
            );


            const imageResult =
                await imageResponse.json();


            if (!imageResponse.ok) {

                alert(
                    imageResult.detail ||
                    "Category updated, but image upload failed."
                );

                modal.classList.remove("open");

                document.body.classList.remove("modal-open");

                window.location.reload();

                return;
            }
        }


        // ==========================================
        // 3. SUCCESS
        // ==========================================

        modal.classList.remove("open");

        document.body.classList.remove("modal-open");

        window.location.reload();


    } catch (error) {

        console.error(
            "Update category error:",
            error
        );

        alert(
            "Something went wrong while updating the category."
        );

    }

});

});
