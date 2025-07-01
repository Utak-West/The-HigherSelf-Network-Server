import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';

// Components
import LoginPage from './components/auth/LoginPage';
import DashboardLayout from './components/layout/DashboardLayout';
import Dashboard from './components/dashboard/Dashboard';
import OrganizationSelector from './components/organization/OrganizationSelector';
import LoadingSpinner from './components/ui/LoadingSpinner';

// Hooks
import { useAuth } from './hooks/useAuth';
import { useOrganization } from './hooks/useOrganization';

// Context
import { AuthProvider } from './contexts/AuthContext';
import { OrganizationProvider } from './contexts/OrganizationContext';
import { ThemeProvider } from './contexts/ThemeContext';

function AppContent() {
  const { user, loading: authLoading, isAuthenticated } = useAuth();
  const { currentOrganization, organizations, loading: orgLoading } = useOrganization();
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    // Initialize app after auth and organization data is loaded
    if (!authLoading && !orgLoading) {
      setIsInitialized(true);
    }
  }, [authLoading, orgLoading]);

  // Show loading spinner while initializing
  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // If not authenticated, show login page
  if (!isAuthenticated) {
    return (
      <AnimatePresence mode="wait">
        <motion.div
          key="login"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
        >
          <LoginPage />
        </motion.div>
      </AnimatePresence>
    );
  }

  // If authenticated but no organization selected, show organization selector
  if (isAuthenticated && organizations.length > 0 && !currentOrganization) {
    return (
      <AnimatePresence mode="wait">
        <motion.div
          key="org-selector"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.3 }}
        >
          <OrganizationSelector />
        </motion.div>
      </AnimatePresence>
    );
  }

  // If authenticated but no organizations, show welcome message
  if (isAuthenticated && organizations.length === 0) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-bold text-foreground">Welcome to Master Dashboard</h1>
          <p className="text-muted-foreground">
            You don't have access to any organizations yet. Please contact your administrator.
          </p>
        </div>
      </div>
    );
  }

  // Main application with dashboard
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key="dashboard"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
        className="min-h-screen bg-background"
      >
        <Routes>
          <Route path="/" element={<DashboardLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="analytics" element={<div>Analytics Page</div>} />
            <Route path="integrations" element={<div>Integrations Page</div>} />
            <Route path="settings" element={<div>Settings Page</div>} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <OrganizationProvider>
          <Router>
            <div className="App">
              <AppContent />
            </div>
          </Router>
        </OrganizationProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;

