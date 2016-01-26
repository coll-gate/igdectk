/**
 * @file csrf.js
 * @brief Utils for CSRF.
 * @author Frederic SCHERMA
 * @date 2016-01-26
 * @copyright Copyright (c) 2016 INRA UMR1095 GDEC
 * @license @todo
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
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

// common ready dom
$(function() {

    //
    // AJAX configuration for CSRF protection
    //

    // $(document).ajaxError(function(event, jqXHR, settings, thrownError) {
    //     data = jqXHR.responseJSON;
    //     if (data.cause) {
    //         error(data.cause);
    //     } else {
    //         error(data);
    //     }
    // });

    $(document).ajaxSend(function(event, jqXHR, settings) {
        // always add the csrf token to safe method ajax query
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            jqXHR.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
        }
    });

    $(document).ajaxComplete(function(event, xhr, settings) {
        // for any form in the page update its csrf token after each safe method call
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            var crsftoken = getCookie('csrftoken');

            $('form').each(function(index, el) {
                $(this).find('input[name="csrfmiddlewaretoken"]').attr('value', crsftoken)
            });
        }
    });
});
