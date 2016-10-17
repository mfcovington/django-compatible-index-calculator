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

// Select all indexes in an index set
$('.btn-select-all').click(function() {
  $(this).closest('.panel').find('.idx').addClass('selected');
});

// Deselect all indexes in an index set
$('.btn-deselect-all').click(function() {
  $(this).closest('.panel').find('.idx').removeClass('selected');
});

// Deselect all indexes
$('.btn-deselect-all-master').click(function() {
  $('.idx').removeClass('selected');
});

// Toggle index sequences
$('.btn-toggle-sequences').click(function() {
  $('.sequence').toggle();
  $('.glyphicon-toggle-sequences').toggle();
});
