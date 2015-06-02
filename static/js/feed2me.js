$(document).ready(function() {

    function display_message(message, level) {
        message_html = '<div class="alert" id="message-div" style="display: none">'
            + '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>'
            + '<span id="message"></span></div>'

        $("#message-div").remove()
        $("#message-placeholder").append(message_html)
        $("#message").text(message)
        $("#message-div").addClass("alert-" + level)
        $("#message-div").show()
    }

    $("#add_feed").on("click", function(event) {
        var feed_url = $("#feed_url").val()
        if (feed_url) {
            $.ajax({
                url: '/feed/',
                type: "POST",
                data: {"feed_url": feed_url}
            }).done(function(data, textStatus, jqXHR) {
                        $("#feeds tbody").append('<tr class="feed">'
                            + '<td style="border-right: 0"><strong>'
                            + data.feed_name 
                            + '</strong><br><span class="feed-url text-muted">'
                            + data.feed_url
                            + '</span></td>'
                            + '<td style="vertical-align: middle; border-left: 0">'
                            + '</td></tr>');
                        $("#no_feeds_message").hide()
                        $("#feed_url").val("")
                        $("#feed_url").focus()
                    })

            .fail(function(jqXHR, textStatus, errorThrown) {
                        if (jqXHR.status == 409) {
                            display_message(jqXHR.responseText, "warning")
                        } else {
                            display_message(jqXHR.responseText, "danger")
                        }
                    })
        }
    });

    function deleteFeed(feed, complete) {
        if (feed) {
            $.ajax({
                url: '/feed/?feed_url=' + encodeURIComponent(feed.find('.feed-url').html()),
                type: "DELETE"
            }).done(function(data, textStatus, jqXHR) {
                        feed.fadeOut('fast', complete)
                    })
            .fail(function(jqXHR, textStatus, errorThrown) {
                      display_message(jqXHR.responseText, "danger")
                  })
        }
    }

    function checkForNoFeeds() {
        // If there are no feeds display a little message
        if ($("#feeds .feed").length == 0) {
            $("#no_feeds_message").show()
        }
    }

    $("#feeds").on("click", function(e) {

        // Get the TR element
        var feedRow = $(e.target).parent('tr')

        // record if this feed is already selected
        selected = feedRow.hasClass("selected");

        // unselect all feeds
        // remove buttons if they exist
        $("#feeds .feed").removeClass("selected");
        $("#feeds .feed #delete-feed-button").remove()

        // if the feed wasn't already selected then select it
        if (!selected) {
            feedRow.addClass("selected");
            feedRow.find('td:last').append($("#delete-button-html").html())
            $("#delete-feed-button").on("click", function(event) {
                deleteFeed(feedRow,
                    function() {
                        feedRow.remove()
                        checkForNoFeeds()
                    })
            });
        }
    });

    // If there are no feeds then display a short message.
    checkForNoFeeds();

    // Set focus on the URL input box when page loads
    $("#feed_url").focus()

});

/*
 * Set the cursor to the busy state when executing an AJAX request.
 */
$(document).ajaxStart(function() {
    $("body").addClass('busy')
});

$(document).ajaxStop(function() {
    $("body").removeClass('busy');
});
