document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("cita-form");

    if (form) {
        form.addEventListener("submit", function (e) {
            // Forzar el envío aunque haya validaciones HTML
            e.preventDefault();
            form.submit();
        });
    }
});
