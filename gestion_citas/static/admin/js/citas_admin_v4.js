(function($) {
    'use strict';

    $(function() {
        console.log("CITAS DEBUG: Script v4 cargado. Forzando eventos...");

        const espField = $('#id_especialidad');
        const centroField = $('#id_centro');
        const medField = $('#id_medico');

        function reset(element) {
            if (element.length) {
                element.empty().append('<option value="">---------</option>').val('').trigger('change.select2');
            }
        }

        // --- 1. Especialidad -> Centro ---
        $(document).on('change', '#id_especialidad', function() {
            const eid = $(this).val();
            console.log("CITAS DEBUG: Especialidad seleccionada ID =", eid);
            
            reset(centroField);
            reset(medField);

            if (eid && eid !== "") {
                console.log("CITAS DEBUG: Solicitando centros para especialidad", eid);
                $.ajax({
                    url: '/ajax/cargar-centros-esp/',
                    data: { 'especialidad_id': eid },
                    dataType: 'json',
                    cache: false,
                    success: function(data) {
                        console.log("CITAS DEBUG: Réponse centros:", data);
                        if (data.centros && data.centros.length > 0) {
                            data.centros.forEach(function(c) {
                                centroField.append($('<option>', { value: c.id, text: c.nombre }));
                            });
                            centroField.trigger('change.select2');
                        } else {
                            console.warn("CITAS DEBUG: No se recibieron centros.");
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error("CITAS DEBUG: Error AJAX Centros:", status, error);
                    }
                });
            }
        });

        // --- 2. Centro -> Médico ---
        $(document).on('change', '#id_centro', function() {
            const cid = $(this).val();
            const eid = $('#id_especialidad').val();
            console.log("CITAS DEBUG: Centro seleccionado ID =", cid, "| Especialidad ID =", eid);
            
            reset(medField);

            if (cid && cid !== "" && eid && eid !== "") {
                console.log("CITAS DEBUG: Solicitando médicos...");
                $.ajax({
                    url: '/ajax/cargar-medicos-esp-centro/',
                    data: { 
                        'especialidad_id': eid,
                        'centro_id': cid
                    },
                    dataType: 'json',
                    cache: false,
                    success: function(data) {
                        console.log("CITAS DEBUG: Réponse médicos:", data);
                        if (data.medicos && data.medicos.length > 0) {
                            data.medicos.forEach(function(m) {
                                medField.append($('<option>', { value: m.id, text: m.nombre }));
                            });
                            medField.trigger('change.select2');
                        } else {
                            console.warn("CITAS DEBUG: No se recibieron médicos.");
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error("CITAS DEBUG: Error AJAX Médicos:", status, error);
                    }
                });
            }
        });
        
        // --- 3. Inicialización Automática (si ya hay algo seleccionado) ---
        // A veces el evento change no se dispara solo al cargar.
        if (espField.val() && espField.val() !== "") {
             console.log("CITAS DEBUG: Detectada selección inicial de especialidad:", espField.val());
             // No disparamos change aquí para evitar bucles, pero si el centro está vacío, podríamos cargar.
        }

    });
})(typeof jQuery !== 'undefined' ? jQuery : (typeof django !== 'undefined' ? django.jQuery : $));
