/**
 * Utilidades de archivar grupo
 * @author German Alzate (Ingeniarte Soft.)
 * @requires jQuery 2.14 or later
 *
 * 2017, German Alzate
 *
 */

;(function($) {

    var methods = {
        init: function (opts) {
            return options = opts;
        },
        reload: function () {
            options = $(this).data('options');
            var $form = $(options.form_selector);
            var $grupo = $getValue(options.grupo_selector);
            var _last_grupo = 0;
            var $csrftoken = $("input[name='csrfmiddlewaretoken']").val();
            var $$ = $(this);
            $.ajax({
                url: options.url_discipulos.replace('0', $grupo),
                method: options.method || 'GET',
                data: $.extend({}, {csrfmiddlewaretoken: $csrftoken}, options.data),
                success: function (data) {
                    // success
                    if (options.override_titles) {
                        $('.replacement-grupo').html('Escoja que desea hacer con los miembros del grupo ' + options.grupo_nombre);
                    }
                    var to_append = '';
                    for (let object of data) {
                        let tr = '<tr>0</tr>';
                        let td = '<td>0</td><td>!</td>';
                        td = td.replace('0', object.pk.toString()).replace('!', (object.fields.nombre + ' ' + object.fields.primer_apellido).toUpperCase());
                        to_append += tr.replace('0', td);
                    }

                    if (to_append.replace(/\s+/g, '')) {
                        $('.hidde-if-not-miembros').css('display', 'inline-table');

                        $$.find(options.table_selector).bootgrid('destroy');
                        $$.find(options.table_selector).find('.insert-miembros').html('').append(to_append);

                        $$.find(options.table_selector).bootgrid({
                            css: {
                                icon: 'zmdi icon',
                                iconColumns: 'zmdi-view-module',
                                iconDown: 'zmdi-expand-more',
                                iconRefresh: 'zmdi-refresh',
                                iconUp: 'zmdi-expand-less'
                            },
                            rowCount: -1,
                            selection: true,
                            multiSelect: true,
                            rowSelect: true,
                            keepSelection: true
                        });
                    } else {
                        $$.find(options.table_selector).bootgrid('destroy');
                        $$.find(options.table_selector).find('.insert-miembros').html('')
                        $('.hidde-if-not-miembros').css('display', 'none');
                    }

                    $$.find(options.modal_selector).modal('show');
                    $('div[data-growl="container"]').remove();

                    $$.find(options.grupo_destino_selector).IGSearch({
                        url: options.url_busqueda.replace('0', $grupo),
                        key: 'grupos',
                        items: [],
                        type: 'GET',
                        messageError: 'Ha ocurrido un error y no se pueden mostrar los grupos',
                    });
                }
            })
            return $$;
        },

        update: function (dict) {
            let options = $.extend({}, $(this).data('options'), dict);
            $(this).removeData('options')
            $(this).data('options', options)
        },

        add_error: function (seleccionados) {
            options = $(this).data('options');
            $(this).carga_miembros('reload');
            $(this).find(options.table_selector).on("loaded.rs.jquery.bootgrid", function(event) {
                $(this).bootgrid('select', seleccionados);
            })
            return $(this);
        }

    }

    function $_ (selector) {
        return (selector.startsWith('.') || selector.startsWith('#')) ? $(selector) : selector;
    }

    function $getValue(selector) {
        return ($_(selector) === selector) ? selector : $_(selector).val().toString();
    }

    $.fn.carga_miembros = function (opts) {
        if (methods[opts]) {
            return methods[opts].apply(this, Array.prototype.slice.call(arguments, 1));
        } else if (typeof opts === 'object' || !opts) {
            return $(this).data('options', $.extend({}, $.fn.carga_miembros.defaults, opts));
        } else {
            console.log('Method ' +  opts + ' does not exist on jQuery.carga_miembros');
        }
    }


    /* Setup plugin defaults */
    $.fn.carga_miembros.defaults = {
        method: 'GET',                                                            // Type of request for AJAX
        messageError: 'Ha ocurrido un error al enviar la peticion',              // Error messages when a error is raised
        data: {},                                                                // Data to send to request
        form_selector: '#formulario-archivar',
        grupo_selector: '#id_grupo',
        grupo_destino_selector: '#id_grupo_destino',
        table_selector: '#table-miembros-eliminar',
        modal_selector: '#modal-eliminar-grupo',
        url_discipulos: '',
        url_busqueda: '',
        grupo_nombre: 'escogido',
        override_titles: true,
    }

})(jQuery);
