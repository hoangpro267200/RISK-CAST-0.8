
(function() {
    'use strict';
    
    const path = window.location.pathname;
    document.querySelectorAll(".nav-link").forEach(a => {
        if (a.getAttribute("href") === path) {
            a.classList.add("active");
        }
    });
})();




















