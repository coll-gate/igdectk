/**
 * @file alert.js
 * @brief Common utils based on JQuery
 * @author Frederic SCHERMA
 * @date 2016-01-26
 * @copyright Copyright (c) 2016 INRA UMR1095 GDEC
 * @license @todo
 */

/**
 * @details Helper to serialize a JQuery object (usually used to serialize a form)
 * If many input have the same name, then the value
 * is stored as an array, with any occurencies.
 * @return {Object} Serialized object
 */
$.fn.serializeObject = function() {
    var o = {};
    var a = this.serializeArray();
    $.each(a, function() {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });
    return o;
};

/**
 * @details Helper to serialize an html form.
 * Depending of the type of an input :
 *     - number are converted to integer value
 *     - checkbox are converted to true/false
 *     - others are kept as string
 *
 * If many input have the same name, then the value
 * is stored as an array, with any occurencies.
 * @return {Object} Serialized object
 * @todo distinct between Number and Integer
 */
$.fn.formToObject = function() {
    var o = {};
    var a = this.find('input');
    $.each(a, function() {
        var value = '';

        if (this.type == "number") {
            value = parseInt(this.value || '');
        } else if (this.type == "checkbox") {
            value = this.checked;
        } else {
            value = this.value || '';
        }

        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(value);
        } else {
            o[this.name] = value;
        }
    });
    return o;
};

// localize and format .datetime to local timezone
(function($) {
    $.fn.localizeDate = function (format) {
        return this.each(function(i) {
            var datestr = $(this).attr("date")/* + " UTC"*/.replace(' ', 'T');
            var datetime = new Date(Date.parse(datestr));
            var fmt = format ? format : 'yy M dd';
            $(this).html($.datepicker.formatDate(fmt, datetime) + ' ' + datetime.toTimeString().split(' ')[0]);
        });
    };
}( jQuery ));

// common ready dom
$(function() {
    // localize and format .datetime to local timezone
    $(".datetime").localizeDate('dd M yy');
});
