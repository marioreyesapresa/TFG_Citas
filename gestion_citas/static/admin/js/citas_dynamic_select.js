(function($) {
    $(document).ready(function() {
        const espSel = $('#id_especialidad');
        const centroSel = $('#id_centro');
        const medSel = $('#id_medico');
        const fechaInp = $('#id_fecha');
        const horaInp = $('#id_hora_inicio');
        
        console.log("CITAS: Script de triple cascada (V3) iniciado.");

        function reset(select) {
            select.empty().append('<option value="">---------</option>').val(null).trigger('change.select2');
        }

        // 1. ESPECIALIDAD -> CENTRO
        espSel.on('change', function() {
            const eid = $(this).val();
            // Solo limpiamos si el cambio es manual
            if (window.isManualChange) {
                reset(centroSel);
                reset(medSel);
            }
            if (eid) {
                $.getJSON('/ajax/cargar-centros-esp/', {especialidad_id: eid}, function(data) {
                    let currentCentro = centroSel.val();
                    centroSel.empty().append('<option value="">---------</option>');
                    data.centros.forEach(c => {
                        centroSel.append(new Option(c.nombre, c.id));
                    });
                    if (currentCentro) centroSel.val(currentCentro);
                    centroSel.trigger('change.select2');
                });
            }
        });

        // 2. CENTRO -> MÉDICO
        centroSel.on('change', function() {
            const cid = $(this).val();
            const eid = espSel.val();
            if (window.isManualChange) {
                reset(medSel);
            }
            if (cid && eid) {
                $.getJSON('/ajax/cargar-medicos-esp-centro/', {especialidad_id: eid, centro_id: cid}, function(data) {
                    let currentMed = medSel.val();
                    medSel.empty().append('<option value="">---------</option>');
                    data.medicos.forEach(m => {
                        medSel.append(new Option(m.nombre, m.id));
                    });
                    if (currentMed) medSel.val(currentMed);
                    medSel.trigger('change.select2');
                });
            }
        });

        // Marcar cambios manuales vs automáticos
        window.isManualChange = true;

        // Carga inicial (Modo Edición o Refresco)
        if (espSel.val()) {
            window.isManualChange = false;
            espSel.trigger('change');
            setTimeout(() => {
                if (centroSel.val()) centroSel.trigger('change');
                window.isManualChange = true;
            }, 500);
        }

        // 3. MÉDICO -> HORARIOS
        if (fechaInp.length && horaInp.length) {
            if (horaInp.is('input')) {
                const hSelect = $('<select></select>', {
                    id: horaInp.attr('id'),
                    name: horaInp.attr('name'),
                    class: horaInp.attr('class'),
                    required: true
                });
                horaInp.replaceWith(hSelect);
            }
            const selHoraFixed = $('#id_hora_inicio');

            function updateHoras(mid, fstr) {
                selHoraFixed.empty().append('<option value="">Buscando...</option>').trigger('change.select2');
                $.getJSON('/ajax/cargar-horas/', {medico: mid, fecha: fstr}, function(data) {
                    let currentH = selHoraFixed.val() || "";
                    selHoraFixed.empty().append('<option value="">-- Selecciona hora --</option>');
                    data.horas.forEach(h => { selHoraFixed.append(new Option(h, h)); });
                    if (currentH) selHoraFixed.val(currentH);
                    selHoraFixed.trigger('change.select2');
                });
            }

            let fp = flatpickr("#id_fecha", {
                locale: "es", minDate: "today", dateFormat: "Y-m-d",
                onChange: function(dates, fstr) {
                    const mid = medSel.val();
                    if (mid && fstr) updateHoras(mid, fstr);
                }
            });
        }
    });
})(typeof jQuery !== 'undefined' ? jQuery : django.jQuery);
