var output = document.getElementById('answer');
var submitButton = document.getElementById('submitButton');
var rejectSubmitButton = document.getElementById('rejectSubmitButton');
var editMessages = document.querySelectorAll('.edit_msg_pen');
var form = document.getElementById('mturk_form');
var audioElements = document.querySelectorAll("audio");
var textareas = document.querySelectorAll("textarea");
var incoherentCheckboxes = document.querySelectorAll(".incoherent-checkboxes");
var expandRules = document.getElementById("expand_rules");
var rules = document.getElementById("rules");
var cleaningRegex = /[^a-zA-Z0-9!?\.,:\[\]\'_-\s]/g
var editor = document.getElementById("editor");
var firstTimeSubmitted = false;



textareas.forEach(function(el) {el.oninput = el.onchange = autosize;});
output.oninput = output.onchange = enableDisableSubmit;


function enableDisableSubmit() {
    output.value = output.value.replace(/<br>/g, ' ').replace(/&nbsp;/g, ' ').replace(cleaningRegex, "");
    if(output.value != '') {
        $("#submitButton").prop("disabled", false);
    } else {
        $("#submitButton").prop("disabled", true);
    }
}


function autosize(el){
    enableDisableSubmit()
    if(el.target) {
        if (el.target.id == 'editor' && el.target.scrollHeight < 60) {
            el.target.style.height = '60px';
        } else {
            el.target.style.height = el.target.scrollHeight + 'px';
        }
    }

}


// add click handler for edit message
if (editMessages) {
    editMessages.forEach(function(msg) {
        var textarea = msg.parentElement.querySelector('textarea');
        textarea.style.height = textarea.scrollHeight + 'px';
        msg.onclick = function() {
            textarea.style.border = '2px solid #fff';
            textarea.disabled = false;
            $(textarea).prop("disabled", false);
            textarea.style.resize = 'vertical';
        }
    })
}


expandRules.onclick = function() {
    rules.style.display = 'block';
    expandRules.style.display = 'none';
}


function placeCaretAtEnd(el) {
    el.focus();
    if (typeof window.getSelection != "undefined"
            && typeof document.createRange != "undefined") {
        var range = document.createRange();
        range.selectNodeContents(el);
        range.collapse(false);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
    } else if (typeof document.body.createTextRange != "undefined") {
        var textRange = document.body.createTextRange();
        textRange.moveToElementText(el);
        textRange.collapse(false);
        textRange.select();
    }
}

function detectIE() {
    var ua = window.navigator.userAgent;

    var msie = ua.indexOf('MSIE ');
    if (msie > 0) {
        // IE 10 or older => return version number
        return parseInt(ua.substring(msie + 5, ua.indexOf('.', msie)), 10);
    }

    var trident = ua.indexOf('Trident/');
    if (trident > 0) {
        // IE 11 => return version number
        var rv = ua.indexOf('rv:');
        return parseInt(ua.substring(rv + 3, ua.indexOf('.', rv)), 10);
    }

    var edge = ua.indexOf('Edge/');
    if (edge > 0) {
       // Edge (IE 12+) => return version number
       return parseInt(ua.substring(edge + 5, ua.indexOf('.', edge)), 10);
    }

    // other browser
    return false;
}

$(function () {

    function updateAnswer() {
        $('#answer').val($('#editor').html().replace(/&nbsp;/g, ' ').replace(/<img .*? data-text="(.+?)".*?>/gm, '[$1]').replace(/<(?:.|\n)*?>/gm, ' ').replace(/\s+/g, ' ').trim().replace(cleaningRegex, ""))
        enableDisableSubmit()
    }


    $('.tag-img').on('click', function() {

        var firstStuff = ''
        if ($('#editor').html()) {
            firstStuff = '&nbsp;'
        }
        $('#editor').html($('#editor').html() + firstStuff + $(this).wrap('<p/>').parent().html() + '&nbsp;')
        $(this).unwrap()
        placeCaretAtEnd($('#editor').get(0));
        $('#editor').focus()
        updateAnswer()
    })

    $('.tag-img').on('dragend', function() {
        $('#editor').html($('#editor').html() + '&nbsp;');
        placeCaretAtEnd($('#editor').get(0));
        $('#editor').focus()
        updateAnswer()

    })
    $('.tag-img').on('dragstart', function() {

        var str = $('#editor').html()
        if (str.substring(str.length - 5, str.length) != '&nbsp;' && str[str.length-1] != ' ') {
            $('#editor').html(str + ' ');
        }
    })

    if($('#answer').val()) $("#submitButton").prop("disabled", false);

    var seenPreview = false;
    // first post to us, then to mturk/next_submit
    $('#mturk_form').on('submit', function(event) {
        $("#submitButton").prop("disabled", true);

        if(!seenPreview) {
            $('#editor .tag-img').each(function() {
                $(this).attr('src', $(this).attr('src') + '?example=true')
            })


            $('.tag-box').html($('.tag-box').data('example-text'))


            var countdown = function(time) {
                $("#submitButton").val('PLEASE PREVIEW YOUR ANSWER (' + time + ')');
                if (time > 0) {
                    setTimeout(function() {
                        countdown(time-1)
                    }, 1000)
                } else {


                    $('#editor .tag-img').each(function() {
                        $(this).attr('src', $(this).attr('src').replace('?example=true', ''))
                    })
                    $('.tag-box').html($('.tag-box').data('tag-text'))
                    seenPreview = true;

                    $("#submitButton").val('Send');
                    $("#submitButton").prop("disabled", false);
                }
            }

            countdown(5)


            return false;
        }

        $('#submitButton', this).attr('disabled', 'disabled');
        if (firstTimeSubmitted) {
            return true;
        } else {
            $("#answer").prop("disabled", false);
            var serialized = $('#mturk_form').serialize();
            $("#answer").prop("disabled", true);
            $.ajax({
                url: "/create_content/submit",
                type: 'post',
                data: serialized,
                success: function(result) {
                    if(result === 'ok') {
                        firstTimeSubmitted = true;
                        $('#mturk_form').submit();
                    }
                }
            });
            return false;
        }
    });





if (detectIE()) {
        $('body').on('focus', '[contenteditable]', function() {
        var $this = $(this);
        $this.data('before', $this.html());
        return $this;
    }).on('blur keyup paste input', '[contenteditable]', function() {
        var $this = $(this);
        if ($this.data('before') !== $this.html()) {
            $this.data('before', $this.html());
            $this.trigger('input');
        }
        return $this;
    });
}








    $('#editor').on('input keyup', function(e) {

        if (e.keyCode === 13) {
              return false;
        }
        seenPreview = false;
        updateAnswer()
        autosize(e)

    })


    $('#rejectSubmitButton').on('click', function() {
        $("#rejectSubmitButton").prop("disabled", true);
        $('#rejectSubmitButton', this).attr('disabled', 'disabled');
        if(!document.querySelector('.incoherent-dialog-box:checked')) return false;
        $.ajax({
            url: "/create_content/reject_submit",
            type: 'post',
            data: $('#mturk_form').serialize(),
            success: function(result) {
                if(result === 'ok') {
                    firstTimeSubmitted = true;
                    $('#mturk_form').submit();
                }
            }
        });
    });

})
