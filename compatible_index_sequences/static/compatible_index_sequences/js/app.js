// Toggle whether index in table is selected when clicked or dragged
// Adapted from: http://stackoverflow.com/a/2014138/996114
$(function () {

  var isMouseDown = false,
    isSetChanged = false,
    isSelected;

  $(".idx")
    .mousedown(function (e) {
      isMouseDown = true;
      isSetChanged = true;
      if (e.shiftKey) {
        deselectIncompatible($(this));
      } else if (e.altKey) {
        if ( $(this).hasClass('incompatible') && $(this).hasClass('selected')) {
          flashIncompatible($(this));
        }
      } else {
        $(this).toggleClass("selected");
        isSelected = $(this).hasClass("selected");
      }
      return false; // prevent text selection
    })
    .mouseover(function (e) {
      if (isMouseDown) {
        if (e.shiftKey) {
          deselectIncompatible($(this));
        } else {
          $(this).toggleClass("selected", isSelected);
        }
      }
    })
    .bind("selectstart", function () {
      return false;
    })

  $(document)
    .mouseup(function () {
      isMouseDown = false;
      if (isSetChanged) {
        checkCompatibility();
        isSetChanged = false;
      }
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
  $('.idx-name').toggleClass('bold');
});

// Toggle manual index length configuration
$('#config-length-manual').click(function() {
  $('#config-length').prop('disabled', function( i, val ) {
    return !val;
  });
  checkCompatibility();
});

// Respond to manual index length changes
$('#config-length').on('change paste keyup', function() {
  checkCompatibility();
});

// Respond to minimum hamming distances changes
$('#config-distance').on('change paste keyup', function() {
  checkCompatibility();
});

// Add tooltip functionality
$(function () {
  $('[data-toggle="tooltip"]').tooltip()
})

// Toggle active index sets
$('#config-visibility :checkbox').change(function() {
  var indexSetId = $(this).attr('index_set_id');
  $('#index_set_' + indexSetId).toggle();
  $('#index_set_' + indexSetId + ' .panel').find('.idx').removeClass('selected');
  checkCompatibility();
});


function hamming(input1, input2, length) {
  if ($('#config-length-manual').is(':checked')) {
    length = $('#config-length')[0].value;
  } else if ( length == null ) {
    length = Math.min(input1.length, input2.length);
  }

  var distance = 0;
  for ( i = 0; i < length; i++ ) {
    if ( input1[ i ] !== input2[ i ] ) {
      distance += 1;
    }
  }
  return distance;
}


function checkCompatibility() {
  var min_dist = $('#config-distance')[0].value;
  var selected = $('.idx.selected');
  var notSelected = $('.idx').not('.selected');
  var incompatible = new Array();

  var s_length = selected.length;
  var n_length = notSelected.length;
  var min_length = minimumIndexLength(selected);

  // compare all members of selected set to self
  for ( var s1 = 0; s1 < s_length; s1++) {
    for ( var s2 = s1 + 1; s2 < s_length; s2++) {
      var sequence1 = $( selected[s1] ).children('.sequence').text().trim();
      var sequence2 = $( selected[s2] ).children('.sequence').text().trim();
      var hamming_distance = hamming(sequence1.toUpperCase(),
                                     sequence2.toUpperCase(), min_length);
      if ( hamming_distance < min_dist ) {
        incompatible.push(selected[s1], selected[s2]);
      }
    }

    // compare all members of selected set to all members of non-selected set
    for ( var n = 0; n < n_length; n++) {
      var sequence1 = $( selected[s1] ).children('.sequence').text().trim();
      var sequence2 = $( notSelected[n] ).children('.sequence').text().trim();
      var hamming_distance = hamming(sequence1.toUpperCase(),
                                     sequence2.toUpperCase(), min_length);
      if ( hamming_distance < min_dist ) {
        incompatible.push(notSelected[n]);
      }
    }
  }

  // Disable select/deselect all buttons when they are irrelevant
  if (s_length > 0) {
    $('.btn-deselect-all-master').prop('disabled', false);
  } else {
    $('.btn-deselect-all-master').prop('disabled', true);
  }

  // Display n-mer length being used for index comparisons
  updateNMerStatus(  s_length, min_length  );

  var indexSetList = $('.index_set');
  for (var i = 0; i < indexSetList.length; i++) {
    var selectedSubset = $(indexSetList[i]).find('.idx.selected');
    var selectAllBtn = $(indexSetList[i]).find('.btn-select-all');
    var deselectAllBtn = $(indexSetList[i]).find('.btn-deselect-all');

    if (selectedSubset.length === 0) {
      $(selectAllBtn).prop('disabled', false);
      $(deselectAllBtn).prop('disabled', true);
    } else if (selectedSubset.length === $(indexSetList[i]).find('.idx').length) {
      $(selectAllBtn).prop('disabled', true);
      $(deselectAllBtn).prop('disabled', false);
    } else {
      $(selectAllBtn).prop('disabled', false);
      $(deselectAllBtn).prop('disabled', false);
    }
  }

  $('.idx').removeClass('incompatible');
  $(incompatible).addClass('incompatible');

  // Enable/Disable Sample Sheet Export Button
  $exportButton = $('#export-csv button[type="submit"]')
  $exportList = $('#export-csv input#id_index_list_csv')[0]
  if ( $('.idx.selected.incompatible').length > 0 ) {
    $exportButton.addClass('btn-danger')
    $exportButton.prop('disabled', true)
  } else if ( $('.idx.selected').length > 0 ) {
    $exportButton.removeClass('btn-danger')
    $exportButton.prop('disabled', false)
    $exportList.value = $.trim($('.idx.selected .sequence').text())
                                                           .split(/\s+/)
                                                           .join(',')
    nameSampleSheet();
  } else {
    $exportButton.removeClass('btn-danger')
    $exportButton.prop('disabled', true)
  }
}


function deselectIncompatible(index) {
  if (!$(index).is('.selected.incompatible')) {
    return;
  }

  var min_dist = $('#config-distance')[0].value;
  var allIndexes = $('.idx');
  var sequence1 = index.children('.sequence').text().trim();

  var min_length = minimumIndexLength($('.idx.selected'));

  for (var i = 0; i < allIndexes.length; i++) {
    if ($(allIndexes[i]).hasClass('selected') && allIndexes[i] !== index[0]) {
      var sequence2 = $(allIndexes[i]).children('.sequence').text().trim();
      var hamming_distance = hamming(sequence1.toUpperCase(),
                                     sequence2.toUpperCase(), min_length);
      if ( hamming_distance < min_dist ) {
        $(allIndexes[i]).removeClass('selected');
      }
    }
  }
}

function flashIncompatible(index) {
  if (!$(index).is('.selected.incompatible')) {
    return;
  }

  var min_dist = $('#config-distance')[0].value;
  var allIndexes = $('.idx');
  var sequence1 = index.children('.sequence').text().trim();

  var min_length = minimumIndexLength($('.idx.selected'));

  var incompatibleSelectedIndexes = $('.idx').filter('.incompatible.selected')
  var indexesToFlash = [];

  for (var i = 0; i < incompatibleSelectedIndexes.length; i++) {
    var sequence2 = $(incompatibleSelectedIndexes[i]).children('.sequence').text().trim();
    var hamming_distance = hamming(sequence1.toUpperCase(),
                                   sequence2.toUpperCase(), min_length);
    if ( hamming_distance < min_dist ) {
      indexesToFlash.push($(incompatibleSelectedIndexes[i]))
    }
  }

  $(indexesToFlash).each(function() {
    $(this)
      .animate({opacity: 0.25}, { duration: 200, queue: true})
      .delay(400)
      .animate({opacity: 1}, { duration: 200, queue: true})
      .delay(200)
      .animate({opacity: 0.25}, { duration: 200, queue: true})
      .delay(400)
      .animate({opacity: 1}, { duration: 200, queue: true})
  });
}

function minimumIndexLength(selected) {
  var sequence_list = $( selected ).children('.sequence').map(function(){
    return $.trim($(this).text());
  }).get();

  var min_length = Infinity;
  for ( var i = 0; i < sequence_list.length; i++ ) {
    min_length = Math.min(min_length, sequence_list[i].length);
  }
  return min_length;
}


function nameSampleSheet() {
  var dateTimeStamp = $.format.toBrowserTimeZone(new Date(), "yyyyMMdd.HHmmss");
  var filename = 'SampleSheet.' + dateTimeStamp + '.csv'
  $('#export-csv input#id_filename')[0].value = filename;
}


function updateNMerStatus( selected_length, min_index_length ) {
  if ($('#config-length-manual').is(':checked')) {
    manual_length = $('#config-length')[0].value;
    if ( manual_length == '' ) {
      manual_length = 'N';
    }
    $('#n-mer').text('\u2014 Comparing ' + manual_length + '-mers');
  } else if (selected_length > 0) {
    $('#n-mer').text('\u2014 Comparing ' + min_index_length + '-mers');
  } else {
    $('#n-mer').text('');
  }
}

$('#feedback-btn').tooltip().eq(0).tooltip('show').tooltip('disable').one('mouseout', function() {
  $(this).tooltip('enable');
});

setTimeout(function() {
  $('#feedback-btn').tooltip().eq(0).tooltip('hide').tooltip('enable');
}, 2000);
