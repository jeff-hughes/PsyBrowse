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

    var addQuery = function(keysValues) {
        for (var key in keysValues) {
            urlQuery[key] = keysValues[key];
        }
        // put URL query string back together
        urlString = '?';
        for (var key in urlQuery) {
            if (urlString !== '?') {
                urlString += '&';
            }
            urlString += key + '=' + urlQuery[key];
        }
        return urlString;
    };


    /* SEARCH PAGE */
    $('.srch-sort').change(function(e) {
        urlString = addQuery({'sort': $(this).val()});
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

    var addFilter = function($elem) {
        var $plus = $elem.find('.srch-filterPlus');
        $elem.addClass('added');
        $plus.animate({opacity: 0}, 100, function() {
            $plus.html('&minus;').animate({opacity: 1}, 100);  
        });
    };

    var removeFilter = function($elem) {
        var $plus = $elem.find('.srch-filterPlus');
        $elem.removeClass('added');
        $plus.animate({opacity: 0}, 100, function() {
            $plus.html('+').animate({opacity: 1}, 100);  
        });
    };

    if ('filter' in urlQuery) {
        var filters = urlQuery['filter'].split('|');
        console.log(filters);
        for (var i in filters) {
            console.log($('.srch-subFilter [data-filter="'+filters[i]+'"]'));
            addFilter($('.srch-subFilter [data-filter="'+filters[i]+'"]').parent());
        }
    }

    $('.srch-subFilter li').click(function(e) {
        e.preventDefault();
        var dataFilter = $(this).children('[data-filter]').attr('data-filter');

        if ($(this).hasClass('added') === false) {
            //addFilter($(this));
            if ('filter' in urlQuery) {
                var filterValue = urlQuery['filter'] + '|' + dataFilter;
            } else {
                var filterValue = dataFilter;
            }
            var urlString = addQuery({'filter': filterValue});
            window.location = urlString;
        } else {
            removeFilter($(this));
            if ('filter' in urlQuery) {
                var ff = urlQuery['filter'];
                var pos = ff.indexOf(dataFilter);
                var length = dataFilter.length;
                if (pos > -1) {
                    if (ff.charAt(pos-1) == '|') {
                        pos--;
                        length++;
                    }
                    var filterValue = ff.substr(0, pos) + ff.substr(pos + length);
                    urlQuery['filter'] = filterValue;
                }
            }
        }
    });

    $('.srch-filterYearText').click(function(e) {
        e.stopPropagation();
    });

    $('.srch-filterYearText').keyup(function(e) {
        if ($(this).val() != '') {
            if ($(this).parent().hasClass('added') === false) {
                addFilter($(this).parent());
            }
        } else {
            if ($(this).parent().hasClass('added') === true) {
                removeFilter($(this).parent());
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