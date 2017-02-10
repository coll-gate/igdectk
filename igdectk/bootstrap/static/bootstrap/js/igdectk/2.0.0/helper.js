/**
 * @file helper.js
 * @brief Popover helper toolbox.
 * @author Frederic SCHERMA
 * @date 2016-01-26
 * @copyright Copyright (c) 2016 INRA UMR1095 GDEC
 * @license @todo
 */

/**
 * @brief Externally triggered popover must use this method to show them (not the default popover('show') method)
 * @param  {Object} object selection
 */
function manualPopoverShow(object) {
    $(".popover-dismiss").each(function(i) { if (this != object[0]) $(this).popover('hide'); });
    object.popover('show');
}

/**
 * @brief Create an helper (tooltip) based on the given dom element.
 * @param  {Object} object dom element
 */
function createHelper(object) {
    var elt = $(object);
    var helper_id = elt.attr("helper-id");
    var helper_inline = elt.children('.helper-content');
    var helper_text = elt.attr("helper-text");
    var helper_title = elt.attr("helper-title");
    var helper_trigger = elt.attr("helper-trigger");
    var template = undefined;

    if (helper_id || helper_text || helper_inline.length) {
        elt.addClass('btn');
        elt.addClass('popover-dismiss')
        elt.addClass('glyphicon glyphicon-question-sign');
        elt.attr('data-toggle', 'popover');

        // not a css because element attribute (over btn style)
        elt.css({
            'top': '-8px',
            'left': '2px',
            'height': '16px',
            'padding': '0px',
            'padding-left': '1px',
            'padding-right': '1px',
            'border': '0px'
        });
    } else if (helper_trigger) {
        elt.addClass('popover-dismiss');
        elt.attr('data-toggle', 'popover');
    }

    if (elt.hasClass("helper-lg"))
        template = '<div class="popover popover-large"><div class="arrow"></div><div class="popover-inner"><h3 class="popover-title"></h3><div class="popover-content"><p></p></div></div></div>'

    if (helper_inline.length) {
        elt.popover({
            html: true,
            placement: 'bottom',
            container: false,  //'body',
            title: helper_title,
            content: helper_inline.html(),
            template: template,
            trigger: 'manual'
        });
    } else if (helper_id) {
        elt.popover({
            html: true,
            placement: 'bottom',
            container: false,  //'body',
            title: helper_title,
            content: $('#' + helper_id).html(),
            template: template,
            trigger: 'manual'
        });
    } else if (helper_text) {
        elt.popover({
            html: false,
            placement: 'bottom',
            container: false,  // 'body',
            title: helper_title,
            content: helper_text,
            template: template,
            trigger: 'manual'
        });
    }

    // because popover button are manually triggered we have to manage it
    if (helper_trigger == null) {
        elt.click(function(e) {
            $(".popover-dismiss").each(function(i) {
                if (this != e.target) {
                    $(this).popover('hide');
                }
            });

            $(this).popover('show');
            return false;
        });
    }
}

// function on jQuery selectors
(function($) {
    $.fn.updateProgressBar = function(min, max, value) {
        this.each(function() {
            var percent = Math.min(((value-min) * 100 / Math.max(max, 1)) + min, 100);
            var el = $(this);
            var progress = el.children('.progress-bar');
            if (progress.length == 0) {
                progress = el;
            }

            //progress.attr({min:min, value:value, max:max});
            progress.css({width: percent + '%'}).attr({
                'aria-valuenow':min,
                'aria-valuenow':value,
                'aria-valuemax':max})
                    .html(percent + '%');

            return el; // support chaining
        });
    };

    $.fn.makePopover = function() {
        this.each(function() {
            var el = $(this);

            createHelper(el);

            return el; // support chaining
        })
    };
}( jQuery ));

// common ready dom
$(function() {
    // initiate any helper tooltips
    $(".helper").each(function(i) {
        createHelper(this);
    });

    // clicking outside of the button hide popover
    $('html').click(function(e) {
        $(".popover-dismiss").popover('hide');
        return true;
    });
});
