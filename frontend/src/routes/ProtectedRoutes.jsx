
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/authContext";

const ProtectedRoutes = ({ allowedRoles }) => {
  const { user, isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
 const allowedRolesArray = allowedRoles || [];
  if (allowedRolesArray.length && !allowedRolesArray.includes(user?.role)) {
    return <Navigate to="/" replace />;
  }


  return <Outlet />;
};

export default ProtectedRoutes;
