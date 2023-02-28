function moveCursorToEnd(id) {
  var el = document.getElementById(id);
  el.focus();
  if (typeof el.selectionStart == "number") {
      el.selectionStart = el.selectionEnd = el.value.length;
  } else if (typeof el.createTextRange != "undefined") {
      var range = el.createTextRange();
      range.collapse(false);
      range.select();
  }
}

function backHistory() {
    javascript:window.history.back();
}

$(document).ready(function () {
    moveCursorToEnd('queryInput');
});