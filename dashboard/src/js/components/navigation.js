// Navigation component - tabs in header
import { setCurrentPage, getState } from '../state/appState.js';

export function renderNavigation(container) {
    const state = getState();
    const currentPage = state.currentPage || 'dashboard';

    console.log('Rendering navigation, current page:', currentPage);

    container.innerHTML = `
        <div class="nav-tabs">
            <button class="nav-tab ${currentPage === 'dashboard' ? 'active' : ''}" data-page="dashboard">
                <span class="nav-tab-text">Dashboard</span>
            </button>
            <button class="nav-tab ${currentPage === 'data' ? 'active' : ''}" data-page="data">
                <span class="nav-tab-text">Data Tables</span>
            </button>
        </div>
    `;

    // Add event listeners
    const navTabs = container.querySelectorAll('.nav-tab');
    console.log('Found nav tabs:', navTabs.length);

    navTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const page = tab.dataset.page;
            console.log('Tab clicked, switching to page:', page);
            setCurrentPage(page);
        });
    });
}
