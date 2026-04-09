import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Toaster } from './components/ui/sonner';
import ErrorBoundary from './pages/ErrorBoundary';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Tenants from './pages/Tenants';
import TenantDetail from './pages/TenantDetail';
import Landlords from './pages/Landlords';
import LandlordDetail from './pages/LandlordDetail';
import Properties from './pages/Properties';
import Contracts from './pages/Contracts';
import Invoices from './pages/Invoices';
import Notifications from './pages/Notifications';
import Reports from './pages/Reports';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import '@/App.css';

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="tenants" element={<Tenants />} />
              <Route path="tenants/:id" element={<TenantDetail />} />
              <Route path="landlords" element={<Landlords />} />
              <Route path="landlords/:id" element={<LandlordDetail />} />
              <Route path="properties" element={<Properties />} />
              <Route path="contracts" element={<Contracts />} />
              <Route path="invoices" element={<Invoices />} />
              <Route path="notifications" element={<Notifications />} />
              <Route path="reports" element={<Reports />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <Toaster position="top-right" richColors />
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
