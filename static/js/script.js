document.addEventListener("DOMContentLoaded", () => {
    const form   = document.getElementById("fraud-form");
    const btn    = document.getElementById("submit-btn");
    if (!form) return;

    form.addEventListener("submit", (e) => {
        let valid = true;

        form.querySelectorAll("input[required]").forEach(input => {
            input.classList.remove("error");
            if (input.value.trim() === "") {
                input.classList.add("error");
                valid = false;
            }
        });

        // Hour validation
        const hour = form.querySelector("input[name='hour_of_day']");
        if (hour && (parseInt(hour.value) < 0 || parseInt(hour.value) > 23)) {
            hour.classList.add("error");
            valid = false;
        }

        if (!valid) {
            e.preventDefault();
            return;
        }

        btn.textContent = "Analysing...";
        btn.disabled = true;
    });
});
