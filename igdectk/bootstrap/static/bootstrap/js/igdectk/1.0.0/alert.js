/**
 * @file alert.js
 * @brief Defines helpers for manipulate info and alert dialogs
 * @author Frederic SCHERMA (INRA UMR 1095)
 * @date 2016-01-26
 * @copyright Copyright (c) 2016 INRA UMR1095
 * @license MIT (see LICENSE file)
 * @details An alert is defined with the @em alert class.
 */

/**
 * Styled alert dialog
 */
function message(style, msg) {
    var message = $('<div>' + '<strong>' + style + ': </strong><span class"message-content">' + msg + '</span></div>');
    $("#messenger").append(message);

    message.on("click", function () { $(this).remove(); });

    message.attr('class', 'alert fade in' + ' alert-' + style)
    var button = $('<button></button>')
        .attr("class", "close")
        .attr("data-dismiss", "alert")
        .attr("aria-hidden", "true")
        .html("&times;");

    message.append(button);

    message.hide().fadeIn(200).delay(2000).fadeOut(1000, function () { $(this).remove(); });
}

/**
 * Add an error alert to the top of the page
 */
function error(msg) {
    message("danger", msg);
}

/**
 * Add a warning alert to the top of the page
 */
function warning(msg) {
    message("warning", msg);
}

/**
 * Add a warning alert to the top of the page
 */
function info(msg) {
    message("info", msg);
}

/**
 * Add a warning alert to the top of the page
 */
function success(msg) {
    message("success", msg);
}

// common ready dom
$(function() {
    // initial message .alert fade out (initiated from Django-Bootstrap)
    $(".alert").each(function(index, val) {
        var msg = $(this);

        msg.on("click", function () { $(this).remove(); });
        msg.hide().fadeIn(200).delay(2000).fadeOut(1000, function () { msg.remove(); });
    });
});
