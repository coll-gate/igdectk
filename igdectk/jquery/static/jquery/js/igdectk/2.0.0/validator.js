/**
 * @file validator.js
 * @brief Field validation helpers using jquery and bootstrap css.
 * @author Frederic SCHERMA (INRA UMR1095)
 * @date 2017-06-28
 * @copyright Copyright (c) 2016 INRA UMR1095
 * @license MIT (see LICENSE file)
 * @details
 */

/**
 * @details For JQuery/Bootstrap form-control, allow to
 * defines the validation state of a form-group.
 * @param  {Object} elt      jquery .form-control element
 * @param  {string} validity 'ok', 'warn' or 'failed'
 * @param  {string} comment  optional comment below the input
 */
function validateInput(elt, validity, comment) {
    let div = elt.parent();

    if (!div.hasClass('has-feedback')) {
        div.addClass('has-feedback');
    }

    let feedback = elt.siblings('span.form-control-feedback');
    if (feedback.length === 0) {
        feedback = $('<span class="form-control-feedback" aria-hidden="true"></span>');
        feedback.addClass($.fn.validator.glyphicon.prefix);

        if ($.fn.validator.className) {
            feedback.addClass($.fn.validator.className);
        }

        div.append(feedback);
    }

    // adjust in case of a select2 element
    if (elt.hasClass('select2-hidden-accessible')) {
        feedback.css('right', '12px');
        feedback.css('top', (feedback.height() - 9) + 'px');
    } else if (div.children('select').length) {
        feedback.css('right', '19px');
    }

    if (validity === 'ok') {
        feedback.removeClass($.fn.validator.glyphicon.warning);
        feedback.removeClass($.fn.validator.glyphicon.failed);
        feedback.addClass($.fn.validator.glyphicon.ok);

        div.removeClass('has-error');
        div.removeClass('has-warning');
        div.addClass('has-success');

        elt.removeClass('invalid');
    } else if (validity === 'warn') {
        feedback.addClass($.fn.validator.glyphicon.warning);
        feedback.removeClass($.fn.validator.glyphicon.failed);
        feedback.removeClass($.fn.validator.glyphicon.ok);

        div.removeClass('has-error');
        div.removeClass('has-success');
        div.addClass('has-warning');

        elt.addClass('invalid');
    } else if (validity === 'failed') {
        feedback.removeClass($.fn.validator.glyphicon.warning);
        feedback.addClass($.fn.validator.glyphicon.failed);
        feedback.removeClass($.fn.validator.glyphicon.ok);

        div.removeClass('has-warning');
        div.removeClass('has-success');
        div.addClass('has-error');

        elt.addClass('invalid');
    } else {
        feedback.removeClass($.fn.validator.glyphicon.warning);
        feedback.removeClass($.fn.validator.glyphicon.failed);
        feedback.removeClass($.fn.validator.glyphicon.ok);

        div.removeClass('has-warning');
        div.removeClass('has-success');
        div.removeClass('has-error');

        elt.addClass('invalid');
    }

    if (comment) {
        let help = elt.siblings('span.help-block');
        if (help.length === 0) {
            help = $('<span class="help-block"></span>');
            div.append(help);
        }
        help.show();
        help.text(comment);
    } else {
        let help = elt.siblings('span.help-block');
        if (help.length > 0) {
            help.hide();
        }
    }
}

// validation function on jQuery selectors
(function($) {
    // clean bootstrap field validator
    $.fn.cleanField = function() {
        this.each(function(){
            validateInput($(this), '', '');
            $(this).val("");

            return $(this); // support chaining
        });
    };

    // fulfill bootstrap field validator
    $.fn.validateField = function (validity, comment) {
        this.each(function(){
            validateInput($(this), validity, comment);

            return $(this); // support chaining
        });
    };

    // is valid field (bootstrap field validator)
    $.fn.isValidField = function () {
        var result = true;

        this.each(function(){
            if ($(this).hasClass('invalid')) {
                result = false;
            }

            return $(this); // support chaining
        });

        return result;
    };

    $.fn.validator = {
        className: undefined,
        glyphicon: {
            'prefix': 'glyphicon',
            'warning': 'glyphicon-refresh',
            'failed': 'glyphicon-remove',
            'ok': 'glyphicon-ok'
        }
    };
})(jQuery);
