// Theme management
$(document).ready(function() {
    const savedTheme = localStorage.getItem('lunaengine-theme') || 'light';
    setTheme(savedTheme);
    
    $('.theme-toggle').click(function() {
        const currentTheme = $('body').attr('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
        localStorage.setItem('lunaengine-theme', newTheme);
    });
    
    $('#moduleSearch').on('input', function() {
        const searchTerm = $(this).val().toLowerCase();
        $('.module-card').each(function() {
            const text = $(this).text().toLowerCase();
            $(this).toggle(text.includes(searchTerm));
        });
    });
});

function setTheme(theme) {
    $('body').attr('data-theme', theme);
    $('.theme-icon').text(theme === 'dark' ? '☀️' : '🌙');
}
