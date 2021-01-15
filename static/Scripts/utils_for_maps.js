if (!String.prototype.format) {
    String.prototype.format = function () {
        string = this.toString();

        for (var x = 0; x < arguments.length; x++) {
            string = string.replace('{' + x.toString() + '}', arguments[x]);
        }

        return string;
    }
}

function clean_direccion(string, _ciudad='Barranquilla') {
    var digit = /(\d{1,3})((([ ]{1})?[a-lA-L]{1}([ ]|\d{1})|([a-lA-L]))?([ ]{1})?(\d{0})?)?/g;

    var _numbers = new Array();
    var regex = digit.exec(string);

    while (regex != null) {
        _numbers.push(regex[0]);
        regex = digit.exec(string);
    }

    if (_numbers.length) {
        var regex_carrera = /([cC](([aArReE]{5,6})|([rRaA]{2})|([rR]{1,2})))|([kK](([aArReE]{5,6})|([rRaA]{2})|([rR]{1,2})))/g;
        var regex_calle = /([cC](([lL]{1,2})|([aAlLeE]{2,4})))/g;
        var regex_avenida = /([dDIiaAGg]{4})((\.)|([oOnNaALl]{4}))?/g;
        var regex_all = /([cC](([aArReE]{5,6})|([rRaA]{2})|([rR]{1,2})))|([kK](([aArReE]{5,6})|([rRaA]{2})|([rR]{1,2})))|([cC](([lL]{1,2})|([aAlLeE]{2,4})))|([dDIiaAGg]{4})((\.)|([oOnNaALl]{4}))?/g;

        var formato = regex_all.exec(string);

        if (formato.length) {
            if (regex_carrera.exec(formato[0]) != null) {
                formato = 'Carrera';
            } else if (regex_calle.exec(formato[0]) != null) {
                formato = 'Calle';
            } else if (regex_avenida.exec(formato[0]) != null) {
                formato = 'Avenida';
            } else {
                throw "Exception with regex, not found any match with 'direccion': " + string;
            }

            try {
                return '{0} {1} # {2} {3}'.format(
                    formato,
                    _numbers[0],
                    _numbers[1],
                    _ciudad
                );
            } catch (error) {
                console.log(error);
            }
        }
    }

    return '';
}