/**
 * Authentication module for API communication.
 */

const API_BASE_URL = 'http://127.0.0.1:5000/api';

export class AuthService {
    static async login(email, password) {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Login failed');
        }

        const data = await response.json();
        if (data.token) {
            localStorage.setItem('auth_token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
        }
        return data;
    }

    static async logout() {
        try {
            await fetch(`${API_BASE_URL}/auth/logout`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${this.getToken()}` },
                credentials: 'include',
            });
        } finally {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user');
            window.location.href = '/src/login.html';
        }
    }

    static getToken() {
        return localStorage.getItem('auth_token');
    }

    static getUser() {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    }

    static isAuthenticated() {
        return !!this.getToken();
    }

    static requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = '/src/login.html';
            return false;
        }
        return true;
    }
}
