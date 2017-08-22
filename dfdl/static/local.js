function enableSave() {
    $('#saveButton').prop('disabled', false);
}

$(document).ajaxError(function (event, jqxhr) {
    var error = 'Something went wrong.';
    try {
        var errobj = jQuery.parseJSON(jqxhr.responseText);
        error = errobj.message;
    } catch (e) {
        error = jqxhr.statusText;
    }
    $("#errmsg").append(error);
    $(".alert").alert().show();
}).ready(function () {
    // Set up the save button
    $('#saveButton').click(function (event) {
        event.preventDefault();
        // Get the textID from the form variable
        var transURL = '/translation/' + $('#idfield').val();
        $.post(transURL, $('#translation').serialize(), function () {
            $('#saveButton').prop('disabled', true)
        });
    });

    // Set up the word lookup popovers
    $(".origword").popover({
        html: true,
        container: 'body',
        placement: 'bottom',
        content: function() {
            var result = $('<div>').addClass('lookup');
            var template = $('#lookuptemplate').html();
            $.get('/lookup/' + this.text, function (resp) {
                $.each(resp, function (i, item) {
                    var card = template;
                    $.each(item, function (k, v) {
                        var tkey = '__' + k.toUpperCase() + '__';
                        card = card.replace(tkey, v);
                    });
                    result.append($(card))
                });
                result.append('<button type="button" class="btn btn-primary" data-toggle="modal" data-target="#addmeaning">Add a definition</button>');
            });
            return result;
        },
        title: function() {
            return "Lookup for " + this.text;
        }
    });

    $(".alert").hide()
});
