/**
 * IGSearch v.1.0
 * @author German Alzate (Ingeniarte Soft.)
 * @requires jQuery 2.14 or later
 *
 * 2016, German Alzate
 *
 * See: http://siiom.conial.net/
 */

;(function ($) {
    $.fn.IGSearch = function (_opts) {

        var _options = $.extend({}, $.fn.IGSearch.defaults, _opts);
        var $URL = _options.url;
        var $DATA = _options.data;
        var _option_tag = _options.option_tag;
        var $$ = $(this);
        var selected_before = _options.items;
        var $csrftoken = $("input[name='csrfmiddlewaretoken']").val();


        var get_in = function (array, value) {
            /*
            Funcion que retorna un indice del array en el caso que el valor pasado como segundo parametro exista
            trabaja con dos tipos de arrays:
            - Array de una dimension
            - Array de dos dimensiones con el valor a buscar en la posicion 0
            */

            for (var i = 0; i < array.length; i++) {
                // recorre el array por indices de tamano
                if (array[i] instanceof Array) {
                    // si es indice sub[i] es un array
                    if (array[i][0].toString() == value.toString()) {
                        // busca en la posicion sub[0] del indice sub[i]
                        return i;
                    }
                } else {
                    // de lo contrario
                    if (array[i].toString() == value.toString()) {
                        // busca normal
                        return i;
                    }
                }
            }

            // si no encuetra nada, retorna falso
            return false;

        }


        var get_different = function (array, list) {
            /*
            Funcion que retorna la diferencia entre dos arrays
            funciona de fos maneras:
            -con arrays de una dimension y
            -arrays de dos dimensiones con el valor a buscar en indice sub[0]
            */

            for (var ind of array) {
                // recorre el array con of
                if (ind instanceof Array) {
                    // si el indice es un array
                    if (get_in(list, ind[0]) === false) {
                        // busca en la otra lista con el indice sub[0]
                        return array.indexOf(ind);  // retorna el indice de el array primero
                    }
                } else {
                    // de lo contrario
                    if (get_in(list, ind) === false) {  // busca en el array segundo
                        return array.indexOf(ind);  // retirna el indice de el array primero
                    }
                }
            }
            // retorna falso de no encontrar nada
            return false;
        }


        var get_jQuery = function (element) {
            /*
            Funcion que retorna el elemento en jquery
            */

            if (element instanceof jQuery) {
                // si ya es jquery
                return element
            }
            // lo convierte a jquery
            return $('#{}'.format(element))
        }


        var get_text_by_option = function (element, value) {
            /*
            Funcion que retorna el html de un elemento option
            */
            var $element = get_jQuery(element);  // obtiene el elemento
            // hace la busqueda
            return $element.find('option[value="' + value.toString() + '"]').html();  // retorna el html
        }


        var get_text_options = function (element) {  // NO TERMINADA
            /*
             * Funcion para retornar las opciones a partir de un texto
            */

            var $element = get_jQuery(element);

            // si es un array
            if ($element.val() instanceof Array) {
                var _list = new Array();
                // obtiene el texto por la opcion
                for (var id of $element.val()) {
                    // lo anade a una lista auxiliar
                    aux = get_text_by_option($element, id);
                    _list.push(aux);
                }
                return _list;
            } else {
                id = $element.val();
                aux = get_text_by_option($element, id);
                return aux;
            }
        }


        var add_selectpicker_options = function (data) {
            /*
            Funcion para agregar las opciones que vienen de ajax a un selectpicker
            */

            var options = '';  // opciones que seran pasadas como html
            var vals = new Array();  // valores que escogera selectpicker para seleccionar opciones
            var $element = $$;  // elemento jQuery para trabajar

            if ($element.attr('multiple')) {  // si es un select multiple
                // global selected_before;
                for (var dict of data) {
                    // recorre los datos
                    option = _option_tag.format(dict['id'], dict['nombre']);  // agrega la opcion con el formato
                    options += option;  // concatena para html
                }
                // selected_before.push([dict['id'], option]);
                if (selected_before.length) {
                    // si existe algo en las selecciones
                    for (_option of selected_before) {
                        // agrega los valores que va a seleccionar
                        vals.push(_option[0].toString());  // todos en string
                        if (!$element.find('option[value="' + _option[0].toString() + '"]').length) {
                            // si no existe ya el elemento option, entonces lo crea (SingleTON)
                            options += _option_tag.format(_option[0], _option[1]);
                        }
                    }
                }
            } else {
                // si no es un select multiple
                for (var dict of data) {
                    // agrega los datos
                    options += _option_tag.format(dict['id'], dict['nombre']);
                }
            }
            // al final, agrega todas las opciones
            $element.html(options).selectpicker('refresh');
            if (vals.length) {
                // si hay algo en vals, lo asigna
                $element.selectpicker('val', vals);
            }
        }

        setTimeout(decorator, 2000);  // se ponen dos segundos de timeout
        function decorator () {
            $$.parent().find('.bs-searchbox input').on('keyup', function (event) {
                /*
                 *En este evento se hacen las peticiones necesarias, de acuerdo a la api actual.
                 */

                // se lanza el prerequest
                var $request = _options.prerequest(_options);

                // si retorna true
                if ($request) {
                    // solo hara peticiones si ya tiene texto
                    if ($(this).val() != '' && $(this).val() != null) {
                        // se crea el ajax
                        $.ajax({
                            url: $URL,  // la url de las opciones
                            data: $.extend(
                                {}, {csrfmiddlewaretoken: $csrftoken, value: $(this).val()}, $DATA
                            ),
                            type: _options.type || 'POST',
                            success: function (data) {
                                // console.log(data) // comment
                                if (data['response_code'] == 200) {
                                    // si la api retorna 200
                                    add_selectpicker_options(data[_options.key]);  // se agregan las opciones
                                    _options.success(data);  // envia el evento de success
                                } else {
                                    danger(_options.messageError);  // muestra el error
                                    _options.error(data);  // envia el evento de error
                                }
                            },
                            error: function (error) {
                                // envia el error directamente
                                danger(_options.messageError);
                                _options.error(error);
                            }
                        });
                    } else {
                        if (!selected_before.length) {
                            // no existen seleccionados
                            // console.log("entre con selected_before_vacio")
                            // limpia el selectpicker
                            $$.html('<option selected value="">NOTHING SELECTED</option>')  // agrega opcion por defecto
                                .selectpicker('refresh');
                        } else {
                            // de lo contrario
                            options = '';
                            vals = new Array();
                            // crea nuevas etiquetas html
                            for (var id of selected_before) {
                                options += _option_tag.format(id[0], id[1]);
                                vals.push(id[0].toString());  // inserta los valores
                            }
                            $$.html(options)  // agrega las opciones
                                .selectpicker('refresh')
                                .selectpicker('val', vals);  // agrega los valores
                        }
                    }
                } else {
                    danger(_options.messageError); // muestra el error
                }
            });
        }


        $$.on('loaded.bs.select', function (e) {
            if ($(this).attr('multiple')) {
                $(this).on('changed.bs.select', function (event, index, new_value, old_value) {
                    // si es un nuevo valor
                    if (new_value) {
                        // busca los datos diferentes para agregar el nuevo
                        difference = get_different($(this).val(), selected_before);
                        if (difference !== false) {
                            // si no existe la diferencia
                            id = $(this).val()[difference];
                            if (get_in(selected_before, id) === false) {
                                // console.log("agrego a {0}".format(get_text_by_option($(this), id)))
                                // agrega la diferencia al arreglo de selecciones
                                selected_before.push([id, get_text_by_option($(this), id)])
                            } else {
                                // pass
                            }
                        } else {
                            // no encuetra diferencias
                            // console.error('No está encontrando diferencias')
                            // pass
                        }
                    } else {
                        // busca el diferente
                        values = $(this).val();
                        // siempre y cuando hayan valores
                        if (values != null || selected_before.length) {
                            if (values == null) {
                                // si los valores estan vacios, se cambia al valor de las selecciones
                                values = selected_before.slice();
                            }
                            // se obtiene el indice del elemento diferente
                            index = get_different(selected_before, values);
                            if (index[0] !== false) {
                                //selected_before.splice(index, 1);
                                // se elimina el elemento que no se usara mas
                                selected_before.splice(index, 1)[0]
                                // console.log("saco a {0}".format(get_text_by_option($(this), selected_before.splice(index, 1)[0])))
                            }
                        }
                    }
                });
            }
        });


        $$.on('hide.bs.select', function (event) {
            // si es multiple
            if ($(this).attr('multiple')) {
                // cuando se esconda el selectpicker
                options_ = '';
                vals = new Array();
                for (var array of selected_before) {
                    //  if (!$(this).find('option[value="' + array[0].toString() + '"]').length) {
                    // agrega todas las opciones
                    options_ += _option_tag.format(array[0], array[1]);
                    // agrega los valores de las opciones para el val de selecpicker
                    vals.push(array[0].toString());
                }
                $(this)
                    .html(options_)  // agrega el html
                    .selectpicker('refresh')
                    .selectpicker('val', vals);  // agrega los valores
            } else {
                // pass
            }
        });

        return $$;

    };


    /* Setup plugin defaults */
    $.fn.IGSearch.defaults = {
        items: new Array(),                                                      // Initial Items
        url: '',                                                                 // URL to request
        type: 'POST',                                                            // Type of request for AJAX
        messageError: 'Ha ocurrido un error al enviar la peticion',              // Error messages when a error is raised
        key: 'key',                                                              // Key contains the main data
        option_tag: '<option value="{0}">{1}</option>',
        data: {},                                                                // Data to send to request
        success: function (data) {return true},                                  // Function to success
        error: function (data) {return true},                                    // Function to error
        prerequest: function (options) {return true},                            //
    }

})(jQuery);
