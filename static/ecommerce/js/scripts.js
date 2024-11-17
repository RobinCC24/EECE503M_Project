document.addEventListener('DOMContentLoaded', () => {
    console.log('E-commerce Scripts Loaded');
    const fetchOrdersButton = document.getElementById('fetch-orders');
    if (fetchOrdersButton) {
        fetchOrdersButton.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/orders');
                const data = await response.json();
                console.log(data);
            } catch (error) {
                console.error('Error fetching orders:', error);
            }
        });
    }
});
