document.addEventListener('DOMContentLoaded', () => {
    console.log('Admin Panel Scripts Loaded');
    const logoutButton = document.querySelector('#logout-btn');
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            alert('Logging out...');
        });
    }
});
