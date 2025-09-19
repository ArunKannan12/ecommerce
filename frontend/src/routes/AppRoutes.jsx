// router.js
import { Suspense, lazy } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import ProtectedRoutes from "./ProtectedRoutes";
import LoadingScreen from "../components/helpers/LoadinScreen";
import { useAuth } from "../contexts/authContext";
const AdminProducts = lazy(()=> import("../components/admin/pages/AdminProducts.jsx"))

// 🔄 Lazy-loaded components
const VisitorHomePage = lazy(() => import("../components/visitor/VisitorHomePage"));
const Home = lazy(() => import("../components/visitor/Home"));
const Store = lazy(() => import("../components/visitor/Store"));
const ProductDetail = lazy(() => import("../components/visitor/ProductDetail"));
const Cart = lazy(() => import("../components/visitor/Cart"));
const Checkout = lazy(() => import("../components/visitor/Checkout"));
const OrderList = lazy(() => import("../components/visitor/OrderList"));
const OrderDetail = lazy(() => import("../components/visitor/OrderDetail"));
const LoginAndSignup = lazy(() => import("../components/visitor/LoginAndSignup"));
const About = lazy(() => import("../components/visitor/About"));
const ReturnRequest = lazy(() => import("../components/visitor/returnReplacement/ReturnRequest.jsx"));
const ReplacementRequest = lazy(() => import("../components/visitor/returnReplacement/ReplacementRequest.jsx"));

const AdminDashboard = lazy(() => import("../components/admin/AdminDashboard"));
const WarehouseDashboard = lazy(() => import("../components/warehousestaff/WarehouseDashboard"));
const DeliveryManDashboard = lazy(() => import("../components/deliveryman/DeliveryManDashboard"));
const ChangePassword = lazy(() => import("../components/visitor/ChangePassword"));
const Profile = lazy(() => import("../components/visitor/Profile"));
const ForgotPassword = lazy(() => import("../components/visitor/ForgotPassword"));
const ConfirmResetPassword = lazy(() => import("../components/visitor/ConfirmResetPassword"));
const ActivateAccount = lazy(() => import("../components/visitor/ActivateAccount"));
const VerifyEmail = lazy(() => import("../components/visitor/VerifyEmail"));
const FacebookAuth = lazy(() => import("../components/visitor/FacebookAuth"));
const GoogleAuth = lazy(() => import("../components/visitor/GoogleAuth"));

const AdminDashboardHome = lazy(()=>import('../components/admin/pages/AdminDashboardHome.jsx'))
// 🌀 Suspense wrapper
const withSuspense = (Component) => (
  <Suspense fallback={<LoadingScreen />}>{Component}</Suspense>
);

// 🚀 Redirect `/` depending on role
const RedirectHome = () => {
  const { isAdmin,isDeliveryMan,isWarehouseStaff } = useAuth();
  
  if (isAdmin()) return <Navigate to="/admin" replace />;
  if (isWarehouseStaff()) return <Navigate to="/warehouse" replace />;
  if (isDeliveryMan()) return <Navigate to="/delivery" replace />;

  // Visitor
  return <VisitorHomePage />;
};

// 🚀 Router setup
export const router = createBrowserRouter([
  // Public routes
  {
    path: "/",
    element: withSuspense(<RedirectHome/>),
    children: [
      { index: true, element: withSuspense(<Home />) },
      { path: "store/", element: withSuspense(<Store />) },
      { path: "store/:categorySlug/", element: withSuspense(<Store />) },
      { path: "products/:productSlug/", element: withSuspense(<ProductDetail />) },
      { path: "cart/", element: withSuspense(<Cart />) },
      { path: "login/", element: withSuspense(<LoginAndSignup />) },
      { path: "about/", element: withSuspense(<About />) },
      { path: "forgot-password/", element: withSuspense(<ForgotPassword />) },
      { path: "/reset-password-confirm/:uid/:token", element: withSuspense(<ConfirmResetPassword />) },
      { path: "/activation/:uid/:token", element: withSuspense(<ActivateAccount />) },
      { path: "/verify-email", element: withSuspense(<VerifyEmail />) },
      { path: "/auth/facebook", element: withSuspense(<FacebookAuth />) },
      { path: "/auth/google", element: withSuspense(<GoogleAuth />) },
    ],
  },

  // Customer routes
  {
    element: <ProtectedRoutes allowedRoles={["customer"]} />,
    children: [
      { path: "/profile", element: withSuspense(<Profile />) },
      { path: "/change-password", element: withSuspense(<ChangePassword />) },
      { path: "checkout/", element: withSuspense(<Checkout />) },
      { path: "orders/", element: withSuspense(<OrderList />) },
      { path: "orders/:id/", element: withSuspense(<OrderDetail />) },
      { path: "returns/create/:orderId", element: withSuspense(<ReturnRequest />) },
      { path: "returns/:returnId", element: withSuspense(<ReturnRequest />) },
      { path: "replacements/create/:orderId", element: withSuspense(<ReplacementRequest />) },
    ],
  },

  // Admin routes
  {
  element: <ProtectedRoutes allowedRoles={["admin"]} />,
  children: [
    {
      path: "/admin",
      element: withSuspense(<AdminDashboard />), // layout
      children: [
        { index: true, element: <Navigate to="/admin/dashboard" replace /> }, // redirect
        { path: "dashboard", element: withSuspense(<AdminDashboardHome />) }, // default on /admin
        { path: "products", element: withSuspense(<AdminProducts/>) },
        // { path: "customers", element: withSuspense(<CustomersAdmin />) },
      ],
    },
    { path: "/profile", element: withSuspense(<Profile />) },
    { path: "/change-password", element: withSuspense(<ChangePassword />) },
  ],
}
,

  // Warehouse routes
  {
    element: <ProtectedRoutes allowedRoles={["warehouse"]} />,
    children: [
      { path: "/warehouse", element: withSuspense(<WarehouseDashboard />) },
      { path: "/profile", element: withSuspense(<Profile />) },
      { path: "/change-password", element: withSuspense(<ChangePassword />) },
    ],
  },

  // Deliveryman routes
  {
    element: <ProtectedRoutes allowedRoles={["deliveryman"]} />,
    children: [
      { path: "/delivery", element: withSuspense(<DeliveryManDashboard />) },
      { path: "/profile", element: withSuspense(<Profile />) },
      { path: "/change-password", element: withSuspense(<ChangePassword />) },
    ],
  },

  // Fallback
  { path: "*", element: withSuspense(<VisitorHomePage />) },
]);
