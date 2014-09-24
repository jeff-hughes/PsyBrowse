$(function() {
    /**
     * Prevents clicked blank links from making all blank links shown as 'visited'.
     */
    $('a').click(function(e) {
        if ($(this).attr('href') == '#') {
            e.preventDefault();
        }
    });


    /**
     * Gets query string from URL and returns object with set of keys and values.
     */
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


    /**
     * Adds argument(s) to the global URL query object; 'keysValues' should be an object with key-value pairs; returns
     * a URL query string
     */
    var addQuery = function(keysValues) {
        for (var key in keysValues) {
            urlQuery[key] = keysValues[key];
        }
        return getQuery();
    };


    /**
     * Reads the global URL query object and returns a query string (e.g., '?var1=x&var2=y'); the optional 'includeEmpty'
     * parameter will include keys with an empty value if set to true. Default value is false.
     */
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


    /* --- INDEX PAGE ----------------------------------------------------------------------------------------------- */

    /**
     * Event handler for the 'load more' button at the bottom of the news feed. When clicked, an AJAX request is sent to
     * load the next page of articles at the bottom of the news feed.
     */
    $('.indx-loadMore').click(function(e) {
        if (jQuery.support.ajax) {
            e.preventDefault();
            var $loadMore = $(this);
            var page = Number($(this).attr('data-page'));
            if (page !== NaN) {
                // AJAX query requests the next page of articles for the news feed, and loads them at the bottom of the
                // news feed
                $.get('/psybrowse/', { 'page': page }, function(data) {
                    if (!('error' in data)) {
                        console.log(data);
                        var feedTemplateSrc = $('#indx_feed_item_template').html();
                        var feedTemplate = Handlebars.compile(feedTemplateSrc);
                        var feedNewHtml = '';
                        if ('articles' in data && data.articles !== null) {
                            // set up template for each article
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
                            // change link to request next page when clicked again
                    } else {
                        // AJAX request returned error
                        console.log(data);
                        $('.indx-pagination').before(
                            '<div class="error indx-error"><strong>Error:</strong> ' + data.error + '</div>'
                        );
                    }
                }).fail(function() {
                    // AJAX request itself did not go through properly
                    console.log('AJAX failure');
                    $('.indx-pagination').before(
                        '<div class="error indx-error"><strong>Error:</strong> There was a problem updating the page. Please try again.</div>'
                    );
                });
            } else {
                $loadMore.parent().html(''); // if page is not set for some reason, just get rid of the button entirely
            }
        }
    });


    /* --- SEARCH PAGE ---------------------------------------------------------------------------------------------- */

    /**
     * These two functions handle animation of filter groups (e.g., Year, Type) when clicked.
     */
    var openFilterGroup = function($elem) {
        $elem.slideDown(200);
    };
    var closeFilterGroup = function($elem) {
        $elem.slideUp(200);
    };


    /**
     * These two functions handle animation of individual filters (e.g., 2014, Article) when added or removed.
     */
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


    /**
     * Takes care of all updates to the page as a result of AJAX requests for the search page. The new results are
     * loaded into a template and inserted onto the page, the pagination is updated, and the display of the number of
     * results is updated (to account for any filters that might narrow the search results).
     */
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


    /**
     * Event handler for sort drop-down menu. When changed, an AJAX request is sent to resort the search results.
     */
    $('.srch-sort').change(function(e) {
        var urlString = addQuery({'sort': $(this).val()});

        if (jQuery.support.ajax) {
            // AJAX query requests search results with new sort argument and replaces the current results with new ones
            $.get('/psybrowse/search/', urlQuery, function(data) {
                if (!('error' in data)) {
                    console.log(data);
                    updateResults(data);
                } else {
                    // AJAX request returned error
                    console.log(data);
                    $('.srch-results').html('<span class="error"><strong>Error:</strong> ' + data.error + '</span>');
                }
            }).fail(function() {
                // AJAX request itself did not go through properly
                console.log('AJAX failure');
                $('.srch-results').html(
                    '<span class="error"><strong>Error:</strong> There was a problem updating the search results. Please try again.</span>'
                );
            });
            addFilter($(this));
        } else {
            // if AJAX is not supported, just go straight to the URL
            window.location = urlString;
        }
    });


    /**
     * This looks through the URL when the page loads,examining any applied filters. It then updates the filter buttons
     * to show the filter has been added.
     */
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


    /**
     * Event handler for filter groups. When clicked, the filter groups open or close.
     */
    $('.srch-filterTitle').click(function(e) {
        e.preventDefault();
        var $subfilter = $(this).parent().find('.srch-subFilter');
        if ($subfilter.is(':hidden')) {
            openFilterGroup($subfilter);
        } else {
            closeFilterGroup($subfilter);
        }
    });


    /**
     * Event handler for filters. When clicked, an AJAX request is sent to either add or remove the filter (depending on
     * its current status).
     */
    $('.srch-subFilter li').click(function(e) {
        e.preventDefault();
        var dataFilter = $(this).children('[data-filter]').attr('data-filter');

        // if filter isn't yet applied, add it
        if ($(this).hasClass('added') === false) {
            // add filter to URL query
            if ('filter' in urlQuery && urlQuery['filter'] != '') {
                var filterValue = urlQuery['filter'] + '|' + dataFilter;
            } else {
                var filterValue = dataFilter;
            }
            var urlString = addQuery({'filter': filterValue});

            if (jQuery.support.ajax) {
                // AJAX request gets filtered results and updates the page with new results
                $.get('/psybrowse/search/', urlQuery, function(data) {
                    if (!('error' in data)) {
                        console.log(data);
                        updateResults(data);
                    } else {
                        // AJAX request returned error
                        console.log(data);
                        $('.srch-results').html('<span class="error"><strong>Error:</strong> ' + data.error + '</span>');
                    }
                }).fail(function() {
                    // AJAX request itself did not go through properly
                    console.log('AJAX failure');
                    $('.srch-results').html(
                        '<span class="error"><strong>Error:</strong> There was a problem updating the search results. Please try again.</span>'
                    );
                });
                addFilter($(this));
            } else {
                // if AJAX is not supported, just go straight to the URL
                window.location = urlString;
            }

        // if filter is already applied, remove it
        } else {
            if ('filter' in urlQuery) {
                // remove filter from URL query
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
                // AJAX request gets unfiltered results and updates the page with new results
                $.get('/psybrowse/search/', urlQuery, function(data) {
                    if (!('error' in data)) {
                        console.log(data);
                        updateResults(data);
                    } else {
                        // AJAX request returned error
                        console.log(data);
                        $('.srch-results').html('<span class="error"><strong>Error:</strong> ' + data.error + '</span>');
                    }
                }).fail(function() {
                    // AJAX request itself did not go through properly
                    console.log('AJAX failure');
                    $('.srch-results').html(
                        '<span class="error"><strong>Error:</strong> There was a problem updating the search results. Please try again.</span>'
                    );
                });
                removeFilter($(this));
            } else {
                // if AJAX is not supported, just go straight to the URL
                window.location = getQuery();
            }
        }
    });


    /**
     * This ensures that when the filter year textboxes are clicked, the filter itself isn't added.
     */
    $('.srch-filterYearText').click(function(e) {
        e.stopPropagation();
    });


    /**
     * Event handler for filter year inputs. When a key is pressed, it updates the data-filter attribute so the filter
     * can be properly applied when added. If the key pressed is Enter, it will automatically add the filter.
     */
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


    /* --- SUBSCRIBE/UNSUBSCRIBE BUTTONS ---------------------------------------------------------------------------- */

    /**
     * Event handler for the subscribe button. When clicked, an AJAX request is sent to subscribe the user to the item
     * on the current page.
     */
    var subscribeHandler = function(e) {
        e.preventDefault();
        var $button = $(this);
        var params = {
            ajax: 'true',
            type: $button.attr('data-type')
        };
        if ($button.attr('data-id')) {
            params['id'] = $button.attr('data-id')
        } else if ($button.attr('data-value')) {
            params['value'] = $button.attr('data-value')
        }

        // AJAX request, if successful, changes the 'subscribe' button to an 'unsubscribe' button and adds the
        // unsubscribe handler to that new button
        $.get('/psybrowse/subscribe/', params, function(data) {
            if (data.response === true) {
                console.log(data);
                $button.removeClass('subbtn-subscribe').addClass('subbtn-unsubscribe');
                var newHref = $button.attr('href').replace('subscribe', 'unsubscribe');
                $button.attr('href', newHref);
                $button.html('Unsubscribe');
                $button.unbind('click', subscribeHandler).bind('click', unsubscribeHandler);
            } else {
                // AJAX request returned error
                console.log(data);
            }
        }).fail(function() {
            // AJAX request itself did not go through properly
            console.log('AJAX failure');
        });
    };


    /**
     * Event handler for the unsubscribe button. When clicked, an AJAX request is sent to unsubscribe the user from the
     * item on the current page.
     */
    var unsubscribeHandler = function(e) {
        e.preventDefault();
        var $button = $(this);
        var params = {
            ajax: 'true',
            type: $button.attr('data-type')
        };
        if ($button.attr('data-id')) {
            params['id'] = $button.attr('data-id')
        } else if ($button.attr('data-value')) {
            params['value'] = $button.attr('data-value')
        }

        // AJAX request, if successful, changes the 'unsubscribe' button to a 'subscribe' button and adds the
        // subscribe handler to that new button
        $.get('/psybrowse/unsubscribe/', params, function(data) {
            if (data.response === true) {
                console.log(data);
                $button.removeClass('subbtn-unsubscribe').addClass('subbtn-subscribe');
                var newHref = $button.attr('href').replace('unsubscribe', 'subscribe');
                $button.attr('href', newHref);
                $button.html('Subscribe');
                $button.unbind('click', unsubscribeHandler).bind('click', subscribeHandler);
            } else {
                // AJAX request returned error
                console.log(data);
            }
        }).fail(function() {
            // AJAX request itself did not go through properly
            console.log('AJAX failure');
        });
    };


    /**
     * This adds the appropriate event handlers to the subscribe and unsubscribe buttons, but only if AJAX is supported.
     * If not, then the button itself is linked to the subscribe/unsubscribe views, which will accomplish the same thing,
     * but with a page reload in between.
     */
    if (jQuery.support.ajax) {
        $('.subbtn-subscribe[data-type]').bind('click', subscribeHandler);
        $('.subbtn-unsubscribe[data-type]').bind('click', unsubscribeHandler);
    }

});