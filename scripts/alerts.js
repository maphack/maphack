function clearAlerts() {
	$('.alert-dismissable').fadeTo(500, 0).slideUp(500, function() {
		$(this).remove();
	});
}

function alertTimeout(wait){
	setTimeout(function(){
		$('#alerts').children('.alert-success:first-child').fadeTo(500, 0).slideUp(500, function() {
			$(this).remove();
		});
	}, wait);
}