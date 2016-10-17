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
      checkCompatibility();
    });
});

// Select all indexes in an index set
$('.btn-select-all').click(function() {
  $(this).closest('.panel').find('.idx').addClass('selected');
  checkCompatibility();
});

// Deselect all indexes in an index set
$('.btn-deselect-all').click(function() {
  $(this).closest('.panel').find('.idx').removeClass('selected');
  checkCompatibility();
});

// Deselect all indexes
$('.btn-deselect-all-master').click(function() {
  $('.idx').removeClass('selected');
  checkCompatibility();
});

// Toggle index sequences
$('.btn-toggle-sequences').click(function() {
  $('.sequence').toggle();
  $('.glyphicon-toggle-sequences').toggle();
});


function hamming(input1, input2) {
  var length = Math.min(input1.length, input2.length);
  var distance = 0;

  for ( i = 0; i < length; i++ ) {
    if ( input1[ i ] !== input2[ i ] ) {
      distance += 1;
    }
  }
  return distance;
}


function checkCompatibility() {
  var min_dist = 3;
  var selected = $('.idx.selected');
  var notSelected = $('.idx').not('.selected');
  var incompatible = new Array();

  var s_length = selected.length;
  var n_length = notSelected.length;

  // compare all members of selected set to self
  for ( var s1 = 0; s1 < s_length; s1++) {
    for ( var s2 = s1 + 1; s2 < s_length; s2++) {
      var sequence1 = $( selected[s1] ).children('.sequence').text().trim();
      var sequence2 = $( selected[s2] ).children('.sequence').text().trim();
      var hamming_distance = hamming(sequence1, sequence2);
      if ( hamming_distance < min_dist ) {
        incompatible.push(selected[s1], selected[s2]);
      }
    }

    // compare all members of selected set to all members of non-selected set
    for ( var n = 0; n < n_length; n++) {
      var sequence1 = $( selected[s1] ).children('.sequence').text().trim();
      var sequence2 = $( notSelected[n] ).children('.sequence').text().trim();
      var hamming_distance = hamming(sequence1, sequence2);
      if ( hamming_distance < min_dist ) {
        incompatible.push(notSelected[n]);
      }
    }
  }

  $('.idx').removeClass('incompatible');
  $(incompatible).addClass('incompatible');
}
