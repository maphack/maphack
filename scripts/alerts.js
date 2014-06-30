function clearAlerts() {
	$('.alert-danger.alert-dismissible').fadeTo(500, 0).slideUp(500, function() {
		$(this).remove();
	});
}

function alertBootstrap(type, message) {
	return '<div class="alert alert-' +
		type + 
		' alert-dismissible" role="alert"><button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">&times;</span><span class="sr-only">close</span></button>' +
		message +
		'</div>'
}

function alertTimeout(wait){
	setTimeout(function(){
		$('#alerts').children('.alert-success:first-child').fadeTo(500, 0).slideUp(500, function() {
			$(this).remove();
		});
	}, wait);
}