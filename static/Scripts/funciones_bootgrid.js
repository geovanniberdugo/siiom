/*
*
* Funciones para solucionar problemas referentes al bootgrid
*
*/

//Funcion para verificar que alguna casilla esté marcada en la tabla
function button_prevent_empty_data ($id_button, $lista_seleccion, $msg) {
    if ($($id_button).length) {
        
        $($id_button).click(function(event) {
            if (!$('tr').hasClass('active')) {
                if ($lista_seleccion.length == 0) {
                    swal($msg);
                    event.preventDefault();
                } else {
                    var $undef = [];
                    var $str = [];
                    for (var i = 0; i < $lista_seleccion.length; i++) {
                        if ($lista_seleccion[i] === undefined) {
                            $undef.push($lista_seleccion[i]);
                        }
                        if (typeof $lista_seleccion[i] === 'string') {
                            $str.push($lista_seleccion[i]);
                        }
                    }
                    if ($str.length > 0) {
                        return true;
                    } else if ($str.length == 0 && $undef.length >= 0) {
                        swal($msg);
                        return false;
                    }
                }
            } else {
                return true;
            }
        });
    } else {
        console.error("El boton no existe");
    }
}


// Funcion para crear inputs[type=hidden] con informacion al servidor
function send_form ($id_form, $lista_seleccion) {

    if ($($id_form).length) {
        $($id_form).submit(function(event) {
            for (var i = 0; i < $lista_seleccion.length; i++) {
                x = $lista_seleccion[i];
                try {
                    $(this).append('<input type="hidden" name="seleccionados" value="' + x.toString() +'">');
                }
                catch(err) {
                    console.log(err);
                }
            }
        });
    } else {
        console.error("El Formulario no existe");
    }    
}


// Funcion para multiselección y empaquetado de datos hacia el servidor
function bootgrid_table_solution ($id_table, $lista_seleccion, $add_button_function=false, $id_button, $msg) {

    if ($($id_table).length) {

        $($id_table).bootgrid().on("loaded.rs.jquery.bootgrid", function(e) {
            var $seleccionados_event_loaded = $lista_seleccion.slice(0);
            $(this).bootgrid('select', $seleccionados_event_loaded);
        });

        $($id_table).bootgrid().on("selected.rs.jquery.bootgrid", function(e, selectedRows) {
            for (var x = 0; x < selectedRows.length; x++) {
                if (typeof selectedRows[x].id === "string") {
                    try {
                        var $index = $lista_seleccion.indexOf(selectedRows[x].id);
                        if ($index != -1) {
                            if (!$index in $lista_seleccion) {
                                $lista_seleccion.push(selectedRows[x].id);
                            } else {
                                console.log("Se evitó que se agreguen datos repetidos");
                            }
                        } else {     
                            $lista_seleccion.push(selectedRows[x].id);
                        }
                    }    
                    catch(err) {
                        console.log(err);
                    }
                }
            }
        });

        $($id_table).bootgrid().on("deselected.rs.jquery.bootgrid", function(e, deselectedRows) {
            for (var x = 0; x < deselectedRows.length; x++) {
                if (typeof deselectedRows[x].id === "string") {
                    var aux2 = $lista_seleccion.indexOf(deselectedRows[x].id);
                    if (aux2 in $lista_seleccion) {
                        $lista_seleccion.splice(aux2,1)
                    }
                }
            }
        });

        if ($add_button_function) {
            button_prevent_empty_data($id_button, $lista_seleccion, $msg);
        }
    } else {
        console.error("La Tabla no existe");
    }
}

