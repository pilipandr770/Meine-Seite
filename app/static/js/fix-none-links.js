/**
 * Script to fix "None" links in product pages
 * This prevents 404 errors when product slugs are missing
 */
document.addEventListener('DOMContentLoaded', function() {
    // Function to fix None links
    function fixNoneLinks() {
        // Find all links pointing to the "None" product
        const noneLinks = document.querySelectorAll('a[href="/shop/product/None"]');
        
        if (noneLinks.length > 0) {
            console.log(`Found ${noneLinks.length} broken "None" links, fixing...`);
            
            noneLinks.forEach(link => {
                // Fix the link by changing href and adding visual indication
                link.setAttribute('href', '#');
                link.classList.add('disabled');
                
                // Optionally add a title attribute to explain why it's disabled
                link.setAttribute('title', 'Product currently unavailable');
                
                // If the link contains an image (common in product cards), add a visual indication
                const productCard = link.closest('.product-card');
                if (productCard) {
                    productCard.style.opacity = '0.7';
                    
                    // Add "Unavailable" label if there's a product name container
                    const nameContainer = productCard.querySelector('.product-name');
                    if (nameContainer) {
                        const badge = document.createElement('span');
                        badge.classList.add('unavailable-badge');
                        badge.textContent = 'Unavailable';
                        badge.style.fontSize = '0.8rem';
                        badge.style.color = '#ff6b6b';
                        badge.style.fontWeight = 'bold';
                        badge.style.marginLeft = '0.5rem';
                        nameContainer.appendChild(badge);
                    }
                }
                
                console.log('Fixed link:', link);
            });
        }
    }
    
    // Run immediately and then again after a delay to catch any dynamically loaded content
    fixNoneLinks();
    setTimeout(fixNoneLinks, 500);
    
    // Also run when AJAX content might be loaded
    document.addEventListener('ajaxComplete', fixNoneLinks);
});
