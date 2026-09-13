document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll(".delete-enquiry-btn").forEach(button => {

        button.addEventListener("click", async () => {

            const enquiryId = button.dataset.enquiryId;

            const confirmed = confirm(
                "Are you sure you want to delete this enquiry?"
            );

            if (!confirmed) {
                return;
            }

            try {

                const response = await fetch(
                    `/admin/enquiries/${enquiryId}`,
                    {
                        method: "DELETE"
                    }
                );

                if (!response.ok) {
                    throw new Error("Failed to delete enquiry");
                }

                button.closest("tr").remove();

            } catch (error) {

                console.error(error);

                alert(
                    "Unable to delete enquiry. Please try again."
                );

            }

        });

    });

});