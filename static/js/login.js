document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const errorMessage = document.getElementById('error-message');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            // Clear previous error messages
            errorMessage.textContent = '';
            errorMessage.style.display = 'none';

            try {
                const response = await fetch('/token', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
                });

                const data = await response.json();

                if (response.ok) {
                    // Store the token in localStorage
                    localStorage.setItem('accessToken', data.access_token);
                    localStorage.setItem('username', username);
                    localStorage.setItem('role', data.role);

                    // Redirect to home page
                    window.location.href = `/home?token=${data.access_token}`;
                } else {
                    // Display error message
                    errorMessage.textContent = data.detail || 'Login failed. Please check your credentials.';
                    errorMessage.style.display = 'block';
                }
            } catch (error) {
                console.error('Login error:', error);
                errorMessage.textContent = 'An error occurred during login. Please try again.';
                errorMessage.style.display = 'block';
            }
        });
    }
}); 