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


    /* INDEX PAGE */
    $('.indx-loadMore').click(function(e) {
        if (jQuery.support.ajax) {
            e.preventDefault();
            var $loadMore = $(this)
            var page = Number($(this).attr('data-page'));
            if (page !== NaN) {
                $.get('/psybrowse/', { 'page': page }, function(data) {
                    if (!('error' in data)) {
                        console.log(data);
                        var feedTemplateSrc = $('#indx_feed_item_template').html();
                        var feedTemplate = Handlebars.compile(feedTemplateSrc);
                        var feedNewHtml = '';
                        if ('articles' in data && data.articles !== null) {
                            for (a in data.articles) {
                                feedNewHtml += feedTemplate(data.articles[a]);
                            }
                            $('.indx-feed').append(feedNewHtml);
                        } else {
                            $('.indx-pagination').html(
                                '<span class="error"><strong>Error:</strong> There was a problem updating the page. Please try again.</span>'
                            );
                        }
                        $loadMore.attr('data-page', page+1).attr('href', '?page='+(page+1));
                    } else {
                        console.log(data);
                        $('.indx-pagination').before(
                            '<div class="error indx-error"><strong>Error:</strong> ' + data.error + '</div>'
                        );
                    }
                }).fail(function() {
                    console.log('AJAX failure');
                    $('.indx-pagination').before(
                        '<div class="error indx-error"><strong>Error:</strong> There was a problem updating the page. Please try again.</div>'
                    );
                });
                addFilter($(this));
            } else {
                $loadMore.parent().html('');
            }
        }
    });


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

    var updateResults = function(data) {
        // update search results list
        var resultsTemplateSrc = $('#srch_result_template').html();
        var resultsTemplate = Handlebars.compile(resultsTemplateSrc);
        var resultsNewHtml = '';
        if ('results' in data && data.results !== null) {
            for (r in data.results) {
                resultsNewHtml += resultsTemplate(data.results[r]);
            }
        } else {
            resultsNewHtml = '<p>Sorry, your search returned no results.</p>';
        }
        $('.srch-results').html(resultsNewHtml);
        $('.hdr-searchInput').val(data.search_term);

        // update pagination
        if ('results' in data && data.results !== null) {
            var paginationTemplateSrc = $('#srch_pagination_template').html();
            var paginationTemplate = Handlebars.compile(paginationTemplateSrc);
            var paginationNewHtml = paginationTemplate(data);
            $('.srch-pagination').html(paginationNewHtml);
        } else {
            $('.srch-pagination').html('');
        }

        // update summary data
        var num_pluralize = (data.num_results == 1) ? '' : 's';
        $('.srch-numResults').html(data.num_results+' result'+num_pluralize);
    };

    $('.srch-subFilter li').click(function(e) {
        e.preventDefault();
        var dataFilter = $(this).children('[data-filter]').attr('data-filter');

        if ($(this).hasClass('added') === false) {
            if ('filter' in urlQuery && urlQuery['filter'] != '') {
                var filterValue = urlQuery['filter'] + '|' + dataFilter;
            } else {
                var filterValue = dataFilter;
            }
            var urlString = addQuery({'filter': filterValue});

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
        } else {
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
                removeFilter($(this));
            } else {
                window.location = getQuery();
            }
        }
    });

    $('.srch-filterYearText').click(function(e) {
        e.stopPropagation();
    });

    $('.srch-filterYearText').keyup(function(e) {
        // if user presses Enter, add filter
        if (e.which == 13) {
            // only triggers if filter has not been added yet; this does not work to remove the filter when input is
            // blank, because the data-filter attribute will be empty
            if ($(this).val() != '' && !$(this).parent().hasClass('added')) {
                $(this).parent().trigger('click');
            }

        // otherwise, update data-filter attribute with current value of input
        } else {
            if ($(this).attr('id') == 'filterYearFrom') {
                var prefix = 'dateFrom:';
            } else if ($(this).attr('id') == 'filterYearTo') {
                var prefix = 'dateTo:';
            }
            var textVal = prefix + $(this).val();
            $(this).parent().children('.srch-subFilterLink').attr('data-filter', textVal);
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

    if (jQuery.support.ajax) {
        $('.subbtn-subscribe[data-type]').bind('click', subscribeHandler);
        $('.subbtn-unsubscribe[data-type]').bind('click', unsubscribeHandler);
    }

});