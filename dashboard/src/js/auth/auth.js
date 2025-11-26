/**
 * Authentication Service (Mock for now)
 */

export const AuthService = {
  /**
   * Get current user from session storage
   */
  getUser() {
    const userStr = sessionStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  /**
   * Set current user in session storage
   */
  setUser(user) {
    sessionStorage.setItem('user', JSON.stringify(user));
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return this.getUser() !== null;
  },

  /**
   * Require authentication (redirect if not authenticated)
   */
  requireAuth() {
    if (!this.isAuthenticated()) {
      // In a real app, redirect to login page
      console.log('User not authenticated, would redirect to login');
      // window.location.href = '/login.html';
    }
  },

  /**
   * Logout user
   */
  logout() {
    sessionStorage.removeItem('user');
    console.log('User logged out');
    // In a real app, redirect to login page
    // window.location.href = '/login.html';
  }
};
