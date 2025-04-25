// static/js/manager_dashboard.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Update active nav link
                document.querySelectorAll('.navbar-nav .nav-link').forEach(navLink => {
                    navLink.classList.remove('active');
                });
                this.classList.add('active');
            }
        });
    });

    // Announcement search functionality
    const announcementSearch = document.getElementById('announcementSearch');
    if (announcementSearch) {
        announcementSearch.addEventListener('input', filterAnnouncements);
    }

    // Announcement category filter
    const categoryFilter = document.getElementById('announcementCategoryFilter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', filterAnnouncements);
    }

    // Task tab memory using localStorage
    const taskTabs = document.getElementById('taskTabs');
    if (taskTabs) {
        // Get last active tab from localStorage
        const lastActiveTab = localStorage.getItem('lastActiveTaskTab');
        if (lastActiveTab) {
            const tabToActivate = document.querySelector(lastActiveTab);
            if (tabToActivate) {
                const tab = new bootstrap.Tab(tabToActivate);
                tab.show();
            }
        }

        // Store active tab on click
        taskTabs.addEventListener('shown.bs.tab', function (e) {
            localStorage.setItem('lastActiveTaskTab', '#' + e.target.id);
        });
    }

    // Set min date for task due date to today
    const taskDueDate = document.getElementById('taskDueDate');
    if (taskDueDate) {
        const today = new Date().toISOString().split('T')[0];
        taskDueDate.setAttribute('min', today);
    }
});

// Filter announcements based on search and category
function filterAnnouncements() {
    const searchTerm = document.getElementById('announcementSearch').value.toLowerCase();
    const categoryFilter = document.getElementById('announcementCategoryFilter').value;
    
    document.querySelectorAll('.announcement-card').forEach(card => {
        const title = card.querySelector('h5').textContent.toLowerCase();
        const content = card.querySelector('.card-text').textContent.toLowerCase();
        const category = card.querySelector('.badge').textContent.trim();
        
        // Check if the card matches both search term and category filter
        const matchesSearch = title.includes(searchTerm) || content.includes(searchTerm);
        const matchesCategory = categoryFilter === '' || category === categoryFilter;
        
        if (matchesSearch && matchesCategory) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Handle form validation
function validateTaskForm() {
    const form = document.getElementById('newTaskForm');
    if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
    }
    form.classList.add('was-validated');
}

// Show notification when task is assigned
function showNotification(message, type = 'info') {
    const notificationContainer = document.getElementById('notificationContainer');
    if (!notificationContainer) {
        // Create notification container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'notificationContainer';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '5000';
        document.body.appendChild(container);
    }
    
    // Create toast notification
    const id = 'toast-' + Date.now();
    const html = `
        <div id="${id}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">Notification</strong>
                <small>Just now</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    document.getElementById('notificationContainer').innerHTML += html;
    
    // Show the toast
    const toastElement = document.getElementById(id);
    const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 5000 });
    toast.show();
    
    // Remove from DOM after hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

// Call this function from server-side events via AJAX response
function updateNotificationBadge(count) {
    const badge = document.querySelector('.leave-notification');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    }
}