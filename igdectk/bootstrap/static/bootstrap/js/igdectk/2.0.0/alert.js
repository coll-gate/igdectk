/**
 * @file alert.js
 * @brief Defines helpers for manipulate info and alert dialogs
 * @author Frederic SCHERMA
 * @date 2016-09-09
 * @copyright Copyright (c) 2016 INRA UMR1095 GDEC
 * @license @todo
 * @details An alert is defined with the @em alert class.
 */

(function($) {
/**
 * Display message alert (info, success, warning, error).
 * Messages are display into the configured container alert.container as jquery element.
 *
 * config.container: jquery element (default is body)
 * config.className: class name for a message (default is alert)
 * config.delay: auto-close delay in milliseconds (0 for infinite) (default is 2000ms)
 */
$.alert = function(config) {
    config = config || {};

    if(typeof config.container == "undefined") {
        config.container = $("body");
    }

    if(typeof config.className == "undefined") {
        config.className = "alert";
    }

    if(typeof config.delay == "undefined") {
        config.delay = 2000;
    }

    $.alert.config = config;
};

$.alert.update = function() {
    // update each alert to support close button and auto-hide in a delay
    $("." + $.alert.config.className).each(function(index, val) {
        var msg = $(this);

        msg.on("click", function () { $(this).remove(); });
        msg.hide().fadeIn(200).delay($.alert.config.delay).fadeOut(1000, function () { msg.remove(); });
    });
};


/**
 * Styled alert dialog
 */
$.alert.message = function(style, msg) {
    var message = $('<div>' + '<strong>' + style + ': </strong><span class"message-content">' + msg + '</span></div>');
    $($.alert.config.container).prepend(message);

    message.on("click", function () { $(this).remove(); });

    message.attr('class', $.alert.config.className + ' fade in' + ' alert-' + style);
    var button = $('<button></button>')
        .attr("class", "close")
        .attr("data-dismiss", "alert")
        .attr("aria-hidden", "true")
        .html("&times;");

    message.append(button);

    message.hide().fadeIn(200).delay($.alert.config.delay).fadeOut(1000, function () { $(this).remove(); });
};

/**
 * Add an error alert to the top of the page
 */
$.alert.error = function(msg) {
    this.message("danger", msg);
};

/**
 * Add a warning alert to the top of the page
 */
$.alert.warning = function(msg) {
    this.message("warning", msg);
};

/**
 * Add a warning alert to the top of the page
 */
$.alert.info = function(msg) {
    this.message("info", msg);
};

/**
 * Add a warning alert to the top of the page
 */
$.alert.success = function(msg) {
    this.message("success", msg);
};

})(jQuery);
