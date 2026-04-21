// Admin Calendar Module
document.addEventListener('DOMContentLoaded', function() {
    const calendarData = JSON.parse((document.getElementById('calendar-data')?.textContent || '[]').trim());
    const modal = document.getElementById('dayModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalList = document.getElementById('modalCitasList');

    // Función para filtrar y normalizar nombres
    function filtrarNombre(nombre) {
        if (!nombre) return "N/A";
        nombre = String(nombre).trim();
        // Eliminar espacios extra
        nombre = nombre.replace(/\s+/g, ' ');
        // Si está vacío después de limpiar, retornar N/A
        return nombre.length === 0 ? "N/A" : nombre;
    }

    function normalizarFecha(fecha) {
        if (!fecha) return '';
        return String(fecha).trim().split('T')[0].split(' ')[0].replace(/\//g, '-');
    }

    // Manejo del clic en días del calendario
    function handleDayClick(fecha, element, esOcupado) {
        if (esOcupado) {
            abrirModal(fecha, element);
        } else {
            toggleBlockDay(fecha, element);
        }
    }

    // Abrir modal con detalles de citas
    function abrirModal(fecha, element) {
        const dia = element.dataset.dia;
        const fechaObjetivo = normalizarFecha(fecha);
        const celda = calendarData.find(c => normalizarFecha(c?.fecha) === fechaObjetivo);
        
        modalTitle.textContent = `Citas del día ${dia} (${fechaObjetivo})`;
        modalList.innerHTML = '';

        if (celda && celda.citas_detalle && celda.citas_detalle.length > 0) {
            celda.citas_detalle.forEach(cita => {
                const hora = cita.hora || "N/A";
                const nombre = filtrarNombre(cita.nombre);
                const div = document.createElement('div');
                div.className = 'modal-cita';
                div.innerHTML = `<p>👤 <strong>${nombre}</strong> | 🕒 ${hora}</p>`;
                modalList.appendChild(div);
            });
        } else {
            modalList.innerHTML = '<p class="no-citas">No hay citas agendadas para este día.</p>';
        }
        modal.classList.add('show');
    }

    // Cerrar modal
    function closeModal() { 
        modal.classList.remove('show'); 
    }

    // Registrar clics por delegacion para que siga funcionando aunque cambie el DOM interno
    const adminCalendar = document.getElementById('adminCalendar');
    if (adminCalendar) {
        adminCalendar.addEventListener('click', (event) => {
            const cell = event.target.closest('.calendar-cell:not(.empty)');
            if (!cell) return;

            const fecha = cell.dataset.date;
            const esOcupado = (cell.dataset.ocupado === 'true');
            handleDayClick(fecha, cell, esOcupado);
        });
    }

    // Alternar estado de disponibilidad de un día
    async function toggleBlockDay(fecha, element) {
        if (element.classList.contains("ocupado")) {
            abrirModal(fecha, element);
            return;
        }

        const currentStatus = element.classList.contains("bloqueado") ? "bloqueado" : "disponible";
        const newStatus = currentStatus === "bloqueado" ? "disponible" : "bloqueado";

        // Actualización visual inmediata (optimista)
        element.classList.remove("disponible", "bloqueado");
        element.classList.add(newStatus);
        element.querySelector(".day-status").textContent = newStatus === "bloqueado" ? "Bloqueado" : "Disponible";

        try {
            const response = await fetch("/admin/toggle_day", {
                method: "POST",
                headers: {"Content-Type": "application/x-www-form-urlencoded"},
                body: new URLSearchParams({fecha: fecha, estado: newStatus})
            });
            if (!response.ok) throw new Error("Error en la respuesta del servidor");
        } catch (err) {
            console.error(err);
            alert("No se pudo actualizar el estado del día. Recargando...");
            location.reload();
        }
    }

    // Eventos del modal
    modal.addEventListener('click', (e) => { 
        if(e.target === modal) closeModal(); 
    });

    document.addEventListener('keydown', (e) => { 
        if(e.key === "Escape") closeModal(); 
    });

    // Manejador del formulario de configuración
    const configForm = document.getElementById('configForm');
    const configMessage = document.getElementById('configMessage');
    
    if (configForm) {
        configForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const duracion = document.getElementById('duracion_cita').value;
            const intervalo = document.getElementById('intervalo_minimo').value;
            
            try {
                const response = await fetch('/admin/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({ duracion, intervalo })
                });
                
                const data = await response.json();
                
                configMessage.style.display = 'block';
                if (response.ok) {
                    configMessage.className = 'success-message';
                    configMessage.textContent = '✓ Configuración actualizada correctamente';
                    configMessage.style.backgroundColor = '#d4edda';
                    configMessage.style.color = '#155724';
                } else {
                    configMessage.className = 'error-message';
                    configMessage.textContent = '✗ ' + (data.error || 'Error al actualizar');
                    configMessage.style.backgroundColor = '#f8d7da';
                    configMessage.style.color = '#721c24';
                }
                
                setTimeout(() => { configMessage.style.display = 'none'; }, 5000);
            } catch (err) {
                console.error(err);
                configMessage.style.display = 'block';
                configMessage.className = 'error-message';
                configMessage.textContent = '✗ Error de conexión';
                configMessage.style.backgroundColor = '#f8d7da';
                configMessage.style.color = '#721c24';
            }
        });
    }

    // Exponer funciones globales para inline handlers
    window.closeModal = closeModal;
});
