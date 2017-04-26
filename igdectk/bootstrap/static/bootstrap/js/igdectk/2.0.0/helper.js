/**
 * @file helper.js
 * @brief Popover helper toolbox.
 * @author Frederic SCHERMA (INRA UMR1095)
 * @date 2016-09-09
 * @copyright Copyright (c) 2016 INRA UMR1095
 * @license MIT (see LICENSE file)
 * @details An alert is defined with the @em alert class.
 */

/**
 * @brief Externally triggered popover must use this method to show them (not the default popover('show') method)
 * @param  {Object} object selection
 */
function manualPopoverShow(object) {
    $(".popover-dismiss").each(function(i) {
        if (this !== object[0]) {
            $(this).popover('hide');
        }
    });

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

            if (progress.length === 0) {
                progress = el;
            }

            //progress.attr({min:min, value:value, max:max});
            progress.css({width: percent + '%'}).attr({
                'aria-valuenow': min,
                'aria-valuenow': value,
                'aria-valuemax': max
            }).html(percent + '%');

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

    /**
     * Swap to elements.
     * @param to Destination of the selected element
     * @returns Element
     */
    $.fn.swapWith = function(to) {
        return this.each(function() {
            // var copyTo = $(to).clone(true);
            // var copyFrom = $(this).clone(true);
            // $(to).replaceWith(copyFrom);
            // $(this).replaceWith(copyTo);

            var parent1, next1,
            parent2, next2;

            parent1 = this.parentNode;
            next1   = this.nextSibling;
            parent2 = to[0].parentNode;
            next2   = to[0].nextSibling;

            parent1.insertBefore(to[0], next1);
            parent2.insertBefore(this, next2);
        });
    };

    /**
     * Check if an element is visible.
     * @returns {boolean}
     */
    $.fn.isInViewport = function() {
        var elementTop = $(this).offset().top;
        var elementBottom = elementTop + $(this).outerHeight();

        var viewportTop = $(window).scrollTop();
        var viewportBottom = viewportTop + $(window).height();

        return elementBottom > viewportTop && elementTop < viewportBottom;
    };
}( jQuery ));

// common ready dom
$(function() {
    // initiate any helper tooltips
    $(".helper").each(function(i) {
        createHelper(this);
    });

    // clicking outside of the button hide popover
    $('body').click(function(e) {
        $(".popover-dismiss").popover('hide');
        return true;
    });
});
