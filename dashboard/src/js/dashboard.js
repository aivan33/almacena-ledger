import { loadDashboardData } from './services/dataService.js';
import { setState, subscribe, getState } from './state/appState.js';
import { renderNavigation } from './components/navigation.js';
import { renderFilters } from './components/filters.js';
import { renderKPIs } from './components/kpis.js';
import { renderCharts, destroyCharts } from './components/charts.js';
import { renderDataTables } from './components/dataTables.js';
import { filterDataByDateRange } from './utils/dataFilter.js';

export async function initDashboard() {
    console.log('Dashboard initializing...');

    const app = document.getElementById('app');

    // Create main structure with navigation in header
    app.innerHTML = `
        <div class="container">
            <div class="header">
                <h1>Trade Finance KPI Dashboard</h1>
                <div id="navigationContainer"></div>
            </div>

            <div id="dataStatus">Loading dashboard data...</div>

            <!-- Dashboard Page -->
            <div id="dashboardPage" class="page-view active">
                <div id="filtersContainer"></div>
                <div id="kpisContainer"></div>
                <div id="chartsContainer"></div>
            </div>

            <!-- Data Tables Page -->
            <div id="dataPage" class="page-view">
                <div id="dataTablesContainer"></div>
            </div>
        </div>
    `;

    try {
        // Load data
        const data = await loadDashboardData();
        console.log('Data loaded successfully:', data);

        // Update state with data and set default page
        setState({ data, currentPage: 'dashboard' });

        // Hide loading message
        document.getElementById('dataStatus').style.display = 'none';

        // Render navigation
        const navigationContainer = document.getElementById('navigationContainer');
        if (navigationContainer) {
            renderNavigation(navigationContainer);
        }

        // Render all components
        renderAllComponents(data);

        // Subscribe to state changes
        let previousState = {
            currency: 'usd',
            viewMode: 'monthly',
            summaryViewMode: 'period',
            dateRangeStart: null,
            dateRangeEnd: null,
            currentPage: 'dashboard'
        };

        subscribe((state) => {
            console.log('State changed:', {
                currency: state.currency,
                viewMode: state.viewMode,
                summaryViewMode: state.summaryViewMode,
                page: state.currentPage
            });

            // Handle page switching
            if (state.currentPage !== previousState.currentPage) {
                console.log('Page changed from', previousState.currentPage, 'to', state.currentPage);
                switchPage(state.currentPage);

                // Re-render navigation to update active state
                const navContainer = document.getElementById('navigationContainer');
                if (navContainer) {
                    renderNavigation(navContainer);
                }
            }

            // Update filter button active states without re-rendering
            updateFilterButtonStates(state);

            // Check if data-affecting state changed
            const dataChanged = state.currency !== previousState.currency ||
                                state.viewMode !== previousState.viewMode ||
                                state.summaryViewMode !== previousState.summaryViewMode ||
                                state.dateRangeStart !== previousState.dateRangeStart ||
                                state.dateRangeEnd !== previousState.dateRangeEnd;

            if (dataChanged) {
                console.log('Re-rendering components (data changed)');

                // Filter data based on date range
                const filteredData = filterDataByDateRange(
                    data,
                    state.dateRangeStart,
                    state.dateRangeEnd
                );

                console.log('Filtered data:', filteredData);

                // Re-render data components
                const kpisContainer = document.getElementById('kpisContainer');
                if (kpisContainer && kpisContainer.closest('.page-view.active')) {
                    renderKPIs(kpisContainer, filteredData);
                }

                destroyCharts();
                const chartsContainer = document.getElementById('chartsContainer');
                if (chartsContainer && chartsContainer.closest('.page-view.active')) {
                    console.log('Rendering charts with data:', filteredData);
                    renderCharts(chartsContainer, filteredData);
                }

                const dataTablesContainer = document.getElementById('dataTablesContainer');
                if (dataTablesContainer && dataTablesContainer.closest('.page-view.active')) {
                    renderDataTables(dataTablesContainer, filteredData);
                }
            }

            previousState = { ...state };
        });

    } catch (error) {
        console.error('Error initializing dashboard:', error);
        document.getElementById('dataStatus').innerHTML = `
            <div style="color: red; padding: 20px; text-align: center;">
                ❌ Error loading dashboard data: ${error.message}
                <br><br>
                <button onclick="window.location.reload()" class="btn-refresh">
                    Retry
                </button>
            </div>
        `;
    }
}

function renderAllComponents(data) {
    // Render filters (dashboard page only)
    const filtersContainer = document.getElementById('filtersContainer');
    if (filtersContainer) {
        renderFilters(filtersContainer);
    }

    // Render KPIs (dashboard page)
    const kpisContainer = document.getElementById('kpisContainer');
    if (kpisContainer) {
        renderKPIs(kpisContainer, data);
    }

    // Render charts (analytics page)
    const chartsContainer = document.getElementById('chartsContainer');
    if (chartsContainer) {
        renderCharts(chartsContainer, data);
    }

    // Render data tables (data page)
    const dataTablesContainer = document.getElementById('dataTablesContainer');
    if (dataTablesContainer) {
        renderDataTables(dataTablesContainer, data);
    }
}

function updateFilterButtonStates(state) {
    // Update currency buttons
    document.querySelectorAll('[data-currency]').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.currency === state.currency);
    });

    // Update view mode buttons
    document.querySelectorAll('[data-view]').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === state.viewMode);
    });

    // Update summary view mode buttons
    document.querySelectorAll('[data-summary]').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.summary === state.summaryViewMode);
    });
}

function switchPage(pageName) {
    console.log('switchPage called with:', pageName);

    // Hide all pages
    const pages = document.querySelectorAll('.page-view');
    pages.forEach(page => {
        page.classList.remove('active');
        console.log('Hiding page:', page.id);
    });

    // Show selected page
    const pageMap = {
        'dashboard': 'dashboardPage',
        'data': 'dataPage'
    };

    const targetPageId = pageMap[pageName];
    const targetPage = document.getElementById(targetPageId);

    console.log('Target page ID:', targetPageId, 'Element:', targetPage);

    if (targetPage) {
        targetPage.classList.add('active');
        console.log('Activated page:', targetPageId);

        // Re-render components for the active page
        const state = getState();
        const filteredData = filterDataByDateRange(
            state.data,
            state.dateRangeStart,
            state.dateRangeEnd
        );

        if (pageName === 'data') {
            const dataTablesContainer = document.getElementById('dataTablesContainer');
            if (dataTablesContainer) {
                renderDataTables(dataTablesContainer, filteredData);
            }
        } else if (pageName === 'dashboard') {
            destroyCharts();
            const chartsContainer = document.getElementById('chartsContainer');
            if (chartsContainer) {
                renderCharts(chartsContainer, filteredData);
            }
        }
    } else {
        console.error('Page not found:', targetPageId);
    }
}
