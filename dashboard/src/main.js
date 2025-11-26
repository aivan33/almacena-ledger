import './css/main.css';
import { initDashboard } from './js/dashboard.js';

console.log('Initializing dashboard...');

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
});
