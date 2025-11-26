/**
 * Login page functionality
 */

import { AuthService } from './auth.js';

const loginForm = document.getElementById('login-form');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const loginBtn = document.getElementById('login-btn');
const loginText = document.getElementById('login-text');
const loginSpinner = document.getElementById('login-spinner');
const alertContainer = document.getElementById('alert-container');

function showAlert(message, type = 'error') {
    alertContainer.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    setTimeout(() => alertContainer.innerHTML = '', 5000);
}

function setLoading(loading) {
    loginBtn.disabled = loading;
    loginText.textContent = loading ? 'Signing in...' : 'Sign In';
    loginSpinner.classList.toggle('hidden', !loading);
    emailInput.disabled = loading;
    passwordInput.disabled = loading;
}

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = emailInput.value.trim();
    const password = passwordInput.value;

    if (!email || !password) {
        showAlert('Please enter both email and password', 'error');
        return;
    }

    setLoading(true);
    alertContainer.innerHTML = '';

    try {
        await AuthService.login(email, password);
        showAlert('Login successful! Redirecting...', 'success');
        setTimeout(() => window.location.href = '/src/index.html', 1000);
    } catch (error) {
        showAlert(error.message || 'Login failed. Please check your credentials.', 'error');
        setLoading(false);
    }
});

if (AuthService.isAuthenticated()) {
    window.location.href = '/src/index.html';
}
