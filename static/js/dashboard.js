// API Helper Functions
const api = {
    token: localStorage.getItem('token'),
    
    async fetch(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json',
            },
        };
        
        const response = await fetch(endpoint, { ...defaultOptions, ...options });
        
        if (response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('token');
            window.location.href = '/login';
            return;
        }
        
        return response;
    },
    
    async get(endpoint) {
        return this.fetch(endpoint);
    },
    
    async post(endpoint, data) {
        return this.fetch(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }
};

// Dashboard Functions
async function loadDashboardStats() {
    try {
        const [patientsResponse, ordersResponse] = await Promise.all([
            api.get('/patients/count'),
            api.get('/orders/pending/count')
        ]);
        
        if (patientsResponse.ok && ordersResponse.ok) {
            const patientsData = await patientsResponse.json();
            const ordersData = await ordersResponse.json();
            
            document.getElementById('total-patients').textContent = patientsData.count;
            document.getElementById('pending-orders').textContent = ordersData.count;
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

// Patient Management
async function loadPatients() {
    try {
        const response = await api.get('/patients');
        if (response.ok) {
            const patients = await response.json();
            const patientsList = document.getElementById('patients-list');
            
            patientsList.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>DOB</th>
                            <th>Gender</th>
                            <th>Contact</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${patients.map(patient => `
                            <tr>
                                <td>${patient.id}</td>
                                <td>${patient.name}</td>
                                <td>${patient.dob}</td>
                                <td>${patient.gender}</td>
                                <td>${patient.contact}</td>
                                <td>
                                    <button onclick="viewPatient(${patient.id})">View</button>
                                    <button onclick="editPatient(${patient.id})">Edit</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }
    } catch (error) {
        console.error('Error loading patients:', error);
    }
}

// Lab Orders
async function loadOrders() {
    try {
        const response = await api.get('/orders');
        if (response.ok) {
            const orders = await response.json();
            const ordersList = document.getElementById('orders-list');
            
            ordersList.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>Order ID</th>
                            <th>Patient</th>
                            <th>Date</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${orders.map(order => `
                            <tr>
                                <td>${order.id}</td>
                                <td>${order.patient_name}</td>
                                <td>${new Date(order.date_ordered).toLocaleDateString()}</td>
                                <td>${order.status}</td>
                                <td>
                                    <button onclick="viewOrder(${order.id})">View</button>
                                    <button onclick="enterResults(${order.id})">Enter Results</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }
    } catch (error) {
        console.error('Error loading orders:', error);
    }
}

// Results Management
async function loadResults() {
    try {
        const response = await api.get('/results');
        if (response.ok) {
            const results = await response.json();
            const resultsList = document.getElementById('results-list');
            
            resultsList.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>Order ID</th>
                            <th>Test</th>
                            <th>Result</th>
                            <th>Unit</th>
                            <th>Reference Range</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${results.map(result => `
                            <tr>
                                <td>${result.order_id}</td>
                                <td>${result.test_name}</td>
                                <td>${result.result_value}</td>
                                <td>${result.unit}</td>
                                <td>${result.reference_range}</td>
                                <td>${result.status}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }
    } catch (error) {
        console.error('Error loading results:', error);
    }
}

// Modal Functions
function showModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function hideModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Set user name
    document.getElementById('username').textContent = localStorage.getItem('username');
    
    // Load initial dashboard data
    loadDashboardStats();
    
    // Navigation
    document.querySelectorAll('.nav-menu a').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            document.querySelectorAll('.nav-menu a').forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Hide all content areas
            document.querySelectorAll('.content-area').forEach(area => area.classList.add('hidden'));
            
            // Show selected content area
            const page = this.dataset.page;
            document.getElementById(`${page}-content`).classList.remove('hidden');
            
            // Load data for the selected page
            switch(page) {
                case 'patients':
                    loadPatients();
                    break;
                case 'orders':
                    loadOrders();
                    break;
                case 'results':
                    loadResults();
                    break;
            }
        });
    });
    
    // Modal close buttons
    document.querySelectorAll('.close').forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            hideModal(modal.id);
        });
    });
    
    // Add Patient Form
    document.getElementById('patient-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const patientData = Object.fromEntries(formData.entries());
        
        try {
            const response = await api.post('/patients', patientData);
            if (response.ok) {
                hideModal('patient-modal');
                loadPatients();
            }
        } catch (error) {
            console.error('Error adding patient:', error);
        }
    });
    
    // Add Order Form
    document.getElementById('order-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const orderData = {
            patient_id: formData.get('patient_id'),
            tests: Array.from(document.querySelectorAll('#test-list input:checked')).map(cb => cb.value)
        };
        
        try {
            const response = await api.post('/orders', orderData);
            if (response.ok) {
                hideModal('order-modal');
                loadOrders();
            }
        } catch (error) {
            console.error('Error creating order:', error);
        }
    });
    
    // Logout
    document.getElementById('logout').addEventListener('click', function(e) {
        e.preventDefault();
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.href = '/login';
    });
}); 