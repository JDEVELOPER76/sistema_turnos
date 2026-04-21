// Home Page - Navigation Logic
document.addEventListener('DOMContentLoaded', function() {
    // ---- Elementos del DOM ----
    const loginBtn = document.getElementById('loginBtnHeader');
    const ctaReservar = document.getElementById('ctaReservar');
    const btnExplorar = document.getElementById('btnExplorar');
    const btnReservarAbajo = document.getElementById('btnReservarAbajo');
    const comoFuncionaSection = document.getElementById('comoFuncionaSection');

    // Función para redirigir a /login
    function redirectToLogin() {
        window.location.href = '/login';
    }

    // Event listeners para botones de login
    loginBtn.addEventListener('click', (e) => {

        redirectToLogin();
    });

    // Event listeners para botones de reserva
    ctaReservar.addEventListener('click', () => {
        redirectToLogin();
    });

    btnReservarAbajo.addEventListener('click', () => {
        redirectToLogin();
    });

    // Scroll suave a sección "Cómo funciona"
    btnExplorar.addEventListener('click', () => {
        comoFuncionaSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
});
