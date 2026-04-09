import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #FAF7F0 0%, #F5F1E8 100%)' }}>
        <div className="text-center">
          <div className="luxury-spinner h-10 w-10 mx-auto" />
          <p className="mt-4" style={{ color: '#8B7355' }}>Caricamento...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;
