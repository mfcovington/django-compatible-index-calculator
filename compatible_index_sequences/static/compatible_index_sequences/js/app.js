// Toggle whether index in table is selected when clicked or dragged
// Adapted from: http://stackoverflow.com/a/2014138/996114
$(function () {

  var isMouseDown = false,
    isSelected;

  $(".idx")
    .mousedown(function () {
      isMouseDown = true;
      $(this).toggleClass("selected");
      isSelected = $(this).hasClass("selected");
      return false; // prevent text selection
    })
    .mouseover(function () {
      if (isMouseDown) {
        $(this).toggleClass("selected", isSelected);
      }
    })
    .bind("selectstart", function () {
      return false;
    })

  $(document)
    .mouseup(function () {
      isMouseDown = false;
    });
});
