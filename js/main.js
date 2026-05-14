(function($) {

	"use strict";

	// Navbar toggle for mobile
	$('.colorlib-nav-toggle').on('click', function(event) {
		event.preventDefault();
		$('body').toggleClass('offcanvas');
		$(this).toggleClass('active');
	});

	// Smooth scrolling for navigation links
	$('a[data-nav-section]').on('click', function(event) {
		event.preventDefault();
		var $this = $(this);
		var section = $this.data('nav-section');
		
		$('#colorlib-main-menu ul li').removeClass('active');
		$this.parent().addClass('active');
		
		$('html, body').animate({
			scrollTop: $('[data-section="' + section + '"]').offset().top - 0
		}, 800, 'easeInOutExpo');
		
		if ($('body').hasClass('offcanvas')) {
			$('body').removeClass('offcanvas');
			$('.colorlib-nav-toggle').removeClass('active');
		}
	});

	// Highlight active section on scroll
	var sections = $('section[data-section]');
	$(window).on('scroll', function() {
		var scrollPos = $(this).scrollTop();
		
		sections.each(function() {
			var $this = $(this);
			var sectionTop = $this.offset().top - 100;
			var sectionBottom = sectionTop + $this.outerHeight();
			
			if (scrollPos >= sectionTop && scrollPos < sectionBottom) {
				var sectionName = $this.data('section');
				$('#colorlib-main-menu ul li').removeClass('active');
				$('#colorlib-main-menu ul li a[data-nav-section="' + sectionName + '"]').parent().addClass('active');
			}
		});
	});

	// Animate elements on scroll
	$(window).on('scroll', function() {
		$('.animate-box').each(function() {
			var $this = $(this);
			if (!$this.hasClass('animated')) {
				if ($(window).scrollTop() + $(window).height() > $this.offset().top) {
					$this.addClass('animated fadeIn');
				}
			}
		});
	});

	$(window).on('load', function() {
		$('.animate-box').each(function() {
			var $this = $(this);
			if ($(window).scrollTop() + $(window).height() > $this.offset().top) {
				$this.addClass('animated fadeIn');
			}
		});
	});

})(jQuery);