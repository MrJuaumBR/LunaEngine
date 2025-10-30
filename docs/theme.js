// LunaEngine Documentation JavaScript

$(document).ready(function() {
    // Theme Toggle
    $('.theme-toggle').click(function() {
        const currentTheme = $('html').attr('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        $('html').attr('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update theme icon
        const themeIcon = $('.theme-icon');
        themeIcon.text(newTheme === 'light' ? '🌙' : '☀️');
    });
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    $('html').attr('data-theme', savedTheme);
    $('.theme-icon').text(savedTheme === 'light' ? '🌙' : '☀️');
    
    // Module Search
    $('#moduleSearch').on('input', function() {
        const searchTerm = $(this).val().toLowerCase();
        
        $('.module-card').each(function() {
            const card = $(this);
            const cardText = card.text().toLowerCase();
            
            if (cardText.includes(searchTerm)) {
                card.show();
            } else {
                card.hide();
            }
        });
    });
    
    // Smooth scrolling for anchor links
    $('a[href^="#"]').on('click', function(event) {
        event.preventDefault();
        const target = $($(this).attr('href'));
        
        if (target.length) {
            $('html, body').animate({
                scrollTop: target.offset().top - 70
            }, 500);
        }
    });
    
    // Add copy to clipboard for code blocks
    $('pre').each(function() {
        const codeBlock = $(this);
        const copyButton = $('<button class="btn btn-sm btn-outline-secondary position-absolute top-0 end-0 m-2">Copy</button>');
        
        codeBlock.css('position', 'relative').append(copyButton);
        
        copyButton.on('click', function() {
            const code = codeBlock.find('code').text() || codeBlock.text();
            navigator.clipboard.writeText(code).then(function() {
                copyButton.text('Copied!');
                setTimeout(() => copyButton.text('Copy'), 2000);
            });
        });
    });
});

// Utility functions
function formatCode(code) {
    return code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
