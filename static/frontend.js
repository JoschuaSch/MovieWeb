window.addEventListener('scroll', function() {
  var navbar = document.getElementById('navbar');
  var header = document.querySelector('.header');
  var headerHeight = header.offsetHeight;

  if (window.pageYOffset >= headerHeight) {
    navbar.classList.add('fixed-navbar');
  } else {
    navbar.classList.remove('fixed-navbar');
  }
});

document.querySelectorAll('.delete-button').forEach(function(button) {
    button.addEventListener('submit', function(e) {
        var confirmation = confirm('Are you sure you want to delete this movie?');
        if (!confirmation) {
            e.preventDefault();
        }
    });
});

