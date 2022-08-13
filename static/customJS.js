$(document).ready( function() {

    var clipboard = $('#copy-button');

    clipboard.on('click', function(e) {
        var text = $("textarea");
        text.select();
        navigator.clipboard.writeText(text.val());
    });

} );