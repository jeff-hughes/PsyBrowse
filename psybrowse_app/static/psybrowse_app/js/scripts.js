$(function() {
    // prevent clicked blank links from making all blank links shown as 'visited'
    $('a').click(function(e) {
        if ($(this).attr('href') == '#') {
            e.preventDefault();
        }
    });

    // gets query string from URL and returns object with set of keys and values
    var urlQuery = (function(a) {
        if (a == '') return {};
        a = a.split('&');
        var b = {};
        for (var i = 0; i < a.length; ++i) {
            var p = a[i].split('=', 2);
            if (p.length == 1)
                b[p[0]] = '';
            else
                b[p[0]] = p[1];
        }
        return b;
    })(window.location.search.substr(1));


    /* SEARCH PAGE */
    $('.srch-sort').change(function(e) {
        urlQuery['sort'] = $(this).val();
        // put URL query string back together
        urlString = '?';
        for (var key in urlQuery) {
            if (urlString !== '?') {
                urlString += '&'
            }
            urlString += key + '=' + urlQuery[key]
        }
        window.location = urlString;
    });

    $('.srch-filterTitle').click(function(e) {
        e.preventDefault();
        var $subfilter = $(this).parent().find('.srch-subFilter');
        if ($subfilter.is(":hidden")) {
            $subfilter.slideDown(200);
            //$(this).find('img').attr('src', 'img/arrow_down.png');
        } else {
            $subfilter.slideUp(200);
            //$(this).find('img').attr('src', 'img/arrow_right.png');
        }
    });

    $('.srch-subFilter li').click(function(e) {
        e.preventDefault();
        var $plus = $(this).find('.srch-filterPlus');
        if ($(this).hasClass('added') === false) {
            $(this).addClass('added');
            $plus.animate({opacity: 0}, 100, function() {
                $plus.html('&minus;')
                    .animate({opacity: 1}, 100);  
            });
        } else {
            $(this).removeClass('added');
            $plus.animate({opacity: 0}, 100, function() {
                $plus.html('+')
                    .animate({opacity: 1}, 100);  
            });
        }
    });

    $('.srch-filterYearText').click(function(e) {
        e.stopPropagation();
    });

    $('.srch-filterYearText').keyup(function(e) {
        var $plus = $(this).parent().find('.srch-filterPlus');
        if ($(this).val() != '') {
            if ($(this).parent().hasClass('added') === false) {
                $(this).parent().addClass('added');
                $plus.animate({opacity: 0}, 100, function() {
                    $plus.html('&minus;')
                        .animate({opacity: 1}, 100);  
                });
            }
        } else {
            if ($(this).parent().hasClass('added') === true) {
                $(this).parent().removeClass('added');
                $plus.animate({opacity: 0}, 100, function() {
                    $plus.html('+')
                        .animate({opacity: 1}, 100);  
                });
            }
        }
    });


    /* SUBSCRIBE BUTTON */
    var subscribeHandler = function(e) {
        e.preventDefault();
        var $button = $(this);
        var params = {
            ajax: 'true',
            type: $button.attr('data-type')
        };
        if ($button.attr('data-id')) {
            params['id'] = $button.attr('data-id')
        }
        else if ($button.attr('data-value')) {
            params['value'] = $button.attr('data-value')
        }
        $.get('/psybrowse/subscribe/', params, function(data) {
            if (data.response === true) {
                console.log(data);
                $button.removeClass('subbtn-subscribe').addClass('subbtn-unsubscribe');
                var newHref = $button.attr('href').replace('subscribe', 'unsubscribe');
                $button.attr('href', newHref);
                $button.html('Unsubscribe');
                $button.unbind('click', subscribeHandler).bind('click', unsubscribeHandler);
            } else {
                console.log(data);
            }
        }).fail(function() {
            console.log('AJAX failure');
        });
    };

    /* UNSUBSCRIBE BUTTON */
    var unsubscribeHandler = function(e) {
        e.preventDefault();
        var $button = $(this);
        var params = {
            ajax: 'true',
            type: $button.attr('data-type')
        };
        if ($button.attr('data-id')) {
            params['id'] = $button.attr('data-id')
        }
        else if ($button.attr('data-value')) {
            params['value'] = $button.attr('data-value')
        }
        $.get('/psybrowse/unsubscribe/', params, function(data) {
            if (data.response === true) {
                console.log(data);
                $button.removeClass('subbtn-unsubscribe').addClass('subbtn-subscribe');
                var newHref = $button.attr('href').replace('unsubscribe', 'subscribe');
                $button.attr('href', newHref);
                $button.html('Subscribe');
                $button.unbind('click', unsubscribeHandler).bind('click', subscribeHandler);
            } else {
                console.log(data);
            }
        }).fail(function() {
            console.log('AJAX failure');
        });
    };

    $('.subbtn-subscribe[data-type]').bind('click', subscribeHandler);
    $('.subbtn-unsubscribe[data-type]').bind('click', unsubscribeHandler);

});