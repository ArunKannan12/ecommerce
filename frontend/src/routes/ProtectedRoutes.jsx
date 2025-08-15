import { useAuth } from "../contexts/AuthContext";
import { Navigate, Outlet, useLocation } from "react-router-dom";

const ProtectedRoutes = ({ allowedRoles }) => {
  const { user, isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  console.log("DEBUG ProtectedRoutes — allowedRoles:", allowedRoles, "user role:", user?.role);
  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoutes;
