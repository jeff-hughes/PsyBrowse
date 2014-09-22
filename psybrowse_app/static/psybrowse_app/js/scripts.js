$(function() {
    // prevent clicked blank links from making all blank links shown as 'visited'
    $('a').click(function(e) {
        if ($(this).attr('href') == '#') {
            e.preventDefault();
        }
    });

    // gets query string from URL and returns object with set of keys and values
    var urlQuery = (function(query) {
        if (query == '') return {};
        query = query.split('&');
        var queryObj = {};
        for (var i = 0; i < query.length; ++i) {
            var keyval = query[i].split('=', 2);
            if (keyval.length == 1)
                queryObj[keyval[0]] = '';
            else
                queryObj[keyval[0]] = decodeURIComponent(keyval[1]);
        }
        return queryObj;
    })(window.location.search.substr(1));

    var addQuery = function(keysValues) {
        for (var key in keysValues) {
            urlQuery[key] = keysValues[key];
        }
        return getQuery();
    };

    var getQuery = function(includeEmpty) {
        includeEmpty = typeof includeEmpty !== 'undefined' ? includeEmpty : false;
        
        var urlString = '?';
        for (var key in urlQuery) {
            if (urlQuery[key] !== '' || includeEmpty) {
                if (urlString !== '?') {
                    urlString += '&';
                }
                urlString += key + '=' + urlQuery[key];
            }
        }
        return urlString;
    }


    /* SEARCH PAGE */
    $('.srch-sort').change(function(e) {
        var urlString = addQuery({'sort': $(this).val()});

        if (jQuery.support.ajax) {
            $.get('/psybrowse/search/', urlQuery, function(data) {
                if (!('error' in data)) {
                    console.log(data);
                    updateResults(data);
                } else {
                    console.log(data);
                    $('.srch-results').html('<span class="error"><strong>Error:</strong> ' + data.error + '</span>');
                }
            }).fail(function() {
                console.log('AJAX failure');
                $('.srch-results').html(
                    '<span class="error"><strong>Error:</strong> There was a problem updating the search results. Please try again.</span>'
                );
            });
            addFilter($(this));
        } else {
            window.location = urlString;
        }
    });

    var openFilterGroup = function($elem) {
        $elem.slideDown(200);
    };

    var closeFilterGroup = function($elem) {
        $elem.slideUp(200);
    };

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
        for (var i in filters) {
            var keyval = filters[i].split(':');
            var $subFilterLi = $('.srch-subFilter [data-filter="'+filters[i]+'"]').parent();

            // special handling for text input of dates
            if (keyval[0] == 'dateFrom') {
                $('#filterYearFrom').val(keyval[1]);
                $subFilterLi = $('#filterYearFrom').parent();
                $subFilterLi.children('.srch-subFilterLink').attr('data-filter', filters[i]);
            } else if (keyval[0] == 'dateTo') {
                $('#filterYearTo').val(keyval[1]);
                $subFilterLi = $('#filterYearTo').parent();
                $subFilterLi.children('.srch-subFilterLink').attr('data-filter', filters[i]);
            }

            addFilter($subFilterLi);
            if ($subFilterLi.parent().is(':hidden')) {
                openFilterGroup($subFilterLi.parent());
            }
        }
    }

    $('.srch-filterTitle').click(function(e) {
        e.preventDefault();
        var $subfilter = $(this).parent().find('.srch-subFilter');
        if ($subfilter.is(':hidden')) {
            openFilterGroup($subfilter);
        } else {
            closeFilterGroup($subfilter);
        }
    });

    $('.srch-subFilter li').click(function(e) {
        e.preventDefault();
        var dataFilter = $(this).children('[data-filter]').attr('data-filter');

        if ($(this).hasClass('added') === false) {
            //addFilter($(this));
            if ('filter' in urlQuery && urlQuery['filter'] != '') {
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
                    if (ff.charAt(pos+length) == '|') {
                        length++;
                    } else if (ff.charAt(pos-1) == '|') {
                        pos--;
                        length++;
                    }
                    var filterValue = ff.substr(0, pos) + ff.substr(pos + length);
                    urlQuery['filter'] = filterValue;
                }
            }
            window.location = getQuery();
        }
    });

    $('.srch-filterYearText').click(function(e) {
        e.stopPropagation();
    });

    $('.srch-filterYearText').keyup(function(e) {
        if ($(this).attr('id') == 'filterYearFrom') {
            var prefix = 'dateFrom:';
        } else if ($(this).attr('id') == 'filterYearTo') {
            var prefix = 'dateTo:';
        }
        var textVal = prefix + $(this).val();
        $(this).parent().children('.srch-subFilterLink').attr('data-filter', textVal);
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