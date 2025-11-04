document.addEventListener('DOMContentLoaded', function () {
  const dropdowns = document.querySelectorAll('.dropdown-toggle');
  
  dropdowns.forEach(dropdown => {
    dropdown.addEventListener('click', function (e) {
      e.preventDefault();
      const menu = this.nextElementSibling;
      const isVisible = menu.classList.contains('show');
      
      document.querySelectorAll('.dropdown-menu.show').forEach(m => m.classList.remove('show'));
      
      if (!isVisible) {
        menu.classList.add('show');
      }
    });
  });

  document.addEventListener('click', function (e) {
    if (!e.target.closest('.dropdown')) {
      document.querySelectorAll('.dropdown-menu.show').forEach(m => m.classList.remove('show'));
    }
  });
});
