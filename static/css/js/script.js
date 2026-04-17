document.addEventListener("DOMContentLoaded", function () {
    let form = document.querySelector("form");

    form.addEventListener("submit", function (event) {
        let amount = document.querySelector("input[name='normalized_amount']");
        let transactionCount = document.querySelector("input[name='transaction_count']");

        // Reset previous error styles
        amount.style.border = "1px solid #ccc";
        transactionCount.style.border = "1px solid #ccc";

        if (amount.value === "" || transactionCount.value === "") {
            alert("🚨 Please fill in all fields before submitting!");

            // Highlight missing fields
            if (amount.value === "") amount.style.border = "2px solid red";
            if (transactionCount.value === "") transactionCount.style.border = "2px solid red";

            event.preventDefault(); // Stops form submission
        } else {
            alert("✅ Processing transaction...");
        }
    });
});