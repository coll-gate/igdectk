/**
 * @file csrf.js
 * @brief Utils for CSRF.
 * @author Frederic SCHERMA (INRA UMR1095)
 * @date 2016-01-26
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
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
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

    //
    // AJAX configuration for CSRF protection
    //

    $(document).ajaxSuccess(function(event, jqXHR, settings, thrownError) {
        // error message on failure
        var data = jqXHR.responseJSON;
        if (data && (typeof(data.cause) !== "string") && data.result && data.result == "failed") {
            alert("!! this should not arrives, please contact your administrator !!");
            error(data.cause);
        }
    });

    $(document).ajaxError(function(event, jqXHR, settings, thrownError) {
        console.log("ajaxError: " + jqXHR.statusText + " " + jqXHR.responseText);

        var data = jqXHR.responseJSON;
        if (data && (typeof(data.cause) === "string")) {
            error(data.cause);
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
