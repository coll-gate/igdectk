/**
 * @file csrf.js
 * @brief Utils for CSRF.
 * @author Frederic SCHERMA (INRA UMR1095)
 * @date 2016-07-04
 * @copyright Copyright (c) 2016 INRA UMR1095
 * @license MIT (see LICENSE file)
 * @details
 */

/**
 * @brief Get a Cookie value according to its name.
 * @param  {string} name Cookie name
 * @return {string}      Cookie value
 */
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Check if a given HTTP method is CSRF safe.
 * In others words, test if an HTTP request using this method
 * doesn't need to contains a CSRF token.
 * @param  {string} method Method type
 * @return {boolean}       true if the method is safe
 */
function csrfSafeMethod(method) {
    // these HTTP methods does not requires CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

// common ready dom
$(function() {

    window.ajaxCount = 0;

    //
    // AJAX configuration for CSRF protection
    //

    $(document).ajaxSuccess(function(event, jqXHR, settings, thrownError) {
        // error message on failure
        var data = jqXHR.responseJSON;
        if (data && (typeof(data.cause) !== "string") && data.result && data.result === "failed") {
            alert("!! this should not arrives, please contact your administrator !!");
            $.alert.error(data.cause);
        }
    });

    $(document).ajaxError(function(event, jqXHR, settings, thrownError) {
        if (jqXHR.statusText && jqXHR.responseText) {
            if (jqXHR.getResponseHeader('Content-Type') === "application/json") {
                console.log("ajaxError: " + jqXHR.statusText + " " + jqXHR.responseText);
            }
        }

        var data = jqXHR.responseJSON;
        if (data) {
            if (typeof(data.cause) === "string") {
                // an single string of cause generate a single alert
                $.alert.error(data.cause);
            } else if (Array.isArray(data.cause)) {
                // an array of cause generate multiple alerts
                for (var i = 0; i < data.cause.length; ++i) {
                    $.alert.error(data.cause[i]);
                }
            } else if (typeof(data.cause) === "object") {
                // an array of cause generate multiple alerts
                for (var k in data.cause) {
                    $.alert.error(k + ": " + data.cause[k]);
                }
            }
        }
    });

    $(document).ajaxSend(function(event, jqXHR, settings) {
        // always add the csrf token to safe method ajax query
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            jqXHR.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
        }
    });

    $(document).ajaxComplete(function(event, jqXHR, settings) {
        // for any form in the page update its csrf token after each safe method call
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            var csrftoken = getCookie('csrftoken');
            $('form').each(function(index, el) {
                $(this).find('input[name="csrfmiddlewaretoken"]').attr('value', csrftoken)
            });
        }
    });
});
