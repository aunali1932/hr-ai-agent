import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './components/Login';
import EmployeeView from './components/EmployeeView';
import HRDashboard from './components/HRDashboard';

const PrivateRoute = ({ children, requiredRole }) => {
  const { user, loading } = useAuth();
  const token = localStorage.getItem('token');

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  if (!token || !user) {
    return <Navigate to="/login" />;
  }

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to={user.role === 'HR' ? '/hr-dashboard' : '/employee'} />;
  }

  return children;
};

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/employee"
        element={
          <PrivateRoute requiredRole="employee">
            <EmployeeView />
          </PrivateRoute>
        }
      />
      <Route
        path="/hr-dashboard"
        element={
          <PrivateRoute requiredRole="HR">
            <HRDashboard />
          </PrivateRoute>
        }
      />
      <Route path="/" element={<Navigate to="/login" />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
}

export default App;


