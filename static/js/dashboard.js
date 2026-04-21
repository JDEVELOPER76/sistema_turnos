/**
 * Dashboard JS Module
 * Maneja la interactividad del calendario, el modal de detalles 
 * y el guardado de citas vía AJAX.
 */
document.addEventListener('DOMContentLoaded', function() {
    // 1. Carga de datos embebidos desde el HTML
    const calendarScript = document.getElementById('calendar-data');
    const citasMesScript = document.getElementById('citas-mes-data');
    
    let calendarData = [];
    let citasMes = [];
    
    try {
        calendarData = JSON.parse(calendarScript?.textContent || '[]');
        citasMes = JSON.parse(citasMesScript?.textContent || '[]');
    } catch (e) {
        console.error('Error al parsear los datos iniciales:', e);
    }

    // 2. Referencias a elementos del DOM
    const modal = document.getElementById('dayModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalList = document.getElementById('modalCitasList');
    const dashboardCalendar = document.getElementById('dashboardCalendar');
    const appointmentForm = document.getElementById('appointmentForm');
    const liveAlert = document.getElementById('liveAlert');
    const totalCitasCount = document.getElementById('totalCitasCount');

    /**
     * Muestra una notificación temporal en el panel
     */
    function showAlert(message, type) {
        if (!liveAlert) return;
        liveAlert.textContent = message;
        liveAlert.className = `alert ${type}`;
        liveAlert.style.display = 'block';
        
        setTimeout(() => {
            liveAlert.style.display = 'none';
        }, 4000);
    }

    /**
     * Sincroniza el estado visual del calendario con el array 'citasMes'
     */
    function refrescarInterfazCalendario() {
        if (!dashboardCalendar) return;

        const cells = dashboardCalendar.querySelectorAll('.calendar-cell:not(.empty)');
        
        cells.forEach(cell => {
            const fechaCelda = cell.dataset.date;
            // Filtrar citas para esta fecha específica
            const citasParaFecha = citasMes.filter(c => c.fecha === fechaCelda);
            
            if (citasParaFecha.length > 0) {
                cell.classList.remove('disponible');
                cell.classList.add('ocupado');
                const statusSpan = cell.querySelector('.day-status');
                if (statusSpan) statusSpan.textContent = `${citasParaFecha.length} cita(s)`;
            }
        });

        // Actualizar el contador global en el stat-card
        if (totalCitasCount) {
            totalCitasCount.textContent = citasMes.length;
        }
    }

    /**
     * Abre el modal y lista las citas de una fecha específica
     */
    function abrirModal(fecha, dia) {
        modalTitle.textContent = `Citas del día ${dia} (${fecha})`;
        modalList.innerHTML = '';

        const citasParaFecha = citasMes.filter(c => c.fecha === fecha);

        if (citasParaFecha.length > 0) {
            citasParaFecha.forEach((cita, index) => {
                const div = document.createElement('div');
                div.className = 'modal-cita';
                div.innerHTML = `
                    <div class="cita-item">
                        <strong>🕒 ${cita.hora}</strong>
                        ${cita.notas ? `<p class="cita-notas">📝 ${cita.notas}</p>` : ''}
                    </div>
                `;
                modalList.appendChild(div);
            });
        } else {
            modalList.innerHTML = `
                <div class="no-citas">
                    ✅ No hay citas para este día.<br>
                    Usa el panel lateral para agendar una.
                </div>`;
        }

        modal.classList.add('show');
    }

    // 3. Manejo de Eventos

    // Click en celdas del calendario para ver detalles
    dashboardCalendar?.addEventListener('click', (e) => {
        const cell = e.target.closest('.calendar-cell:not(.empty)');
        if (!cell || cell.classList.contains('bloqueado')) return;

        const fecha = cell.dataset.date;
        const dia = cell.dataset.dia;
        abrirModal(fecha, dia);
    });

    // Envío del formulario vía AJAX (Fetch)
    appointmentForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(appointmentForm);
        
        try {
            const response = await fetch('/dashboard_save', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();

            if (response.ok) {
                // Actualizar el estado local sin recargar
                citasMes.push({
                    fecha: formData.get('fecha'),
                    hora: formData.get('hora'),
                    notas: formData.get('notas')
                });
                
                refrescarInterfazCalendario();
                showAlert("Cita guardada correctamente", "success");
                appointmentForm.reset();
            } else {
                showAlert(result.message || "Error al guardar la cita", "error");
            }
        } catch (error) {
            console.error('Error en la petición:', error);
            showAlert("Error de conexión con el servidor", "error");
        }
    });

    // 4. Funciones de Cierre de Modal
    window.closeModal = function() {
        if (modal) modal.classList.remove('show');
    };

    // Cerrar al hacer clic fuera del cuadro blanco
    modal?.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    // Cerrar con tecla Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === "Escape") closeModal();
    });

    // Inicialización visual
    refrescarInterfazCalendario();
});