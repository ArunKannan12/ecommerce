import { createBrowserRouter } from "react-router-dom";
import ProtectedRoutes from "./ProtectedRoutes";

// Visitor Pages
import VisitorHomePage from "../components/visitor/VisitorHomePage";
import Home from "../components/visitor/Home";
import Store from "../components/visitor/Store";
import ProductDetail from "../components/visitor/ProductDetail";
import Cart from "../components/visitor/Cart";
import Checkout from "../components/visitor/Checkout";
import OrderList from "../components/visitor/OrderList";
import OrderDetail from "../components/visitor/OrderDetail";
import LoginAndSignup from "../components/visitor/LoginAndSignup";
import About from "../components/visitor/About";

// Dashboards
import CustomerDashboard from "../components/customer/CustomerDashboard";
import AdminDashboard from "../components/admindashboard/AdminDashboard";
import InvestorDashboard from "../components/investor/InvestorDashboard";
import PromoterDashboard from "../components/promoter/PromoterDashboard";
import WarehouseDashboard from "../components/warehousestaff/WarehouseDashboard";
import DeliveryManDashboard from "../components/deliveryman/DeliveryManDashboard";

// Auth / password / activation
import ChangePassword from "../components/visitor/ChangePassword";
import ResetPassword from "../components/visitor/ConfirmResetPassword";
import FacebookAuth from "../components/visitor/FacebookAuth";
import GoogleAuth from "../components/visitor/GoogleAuth";
import ActivateAccount from "../components/visitor/ActivateAccount";
import VerifyEmail from "../components/visitor/VerifyEmail";
import ForgotPassword from "../components/visitor/ForgotPassword";
import ConfirmResetPassword from "../components/visitor/ConfirmResetPassword";

export const router = createBrowserRouter([
  // Public + shared layout with Navbar
  {
    path: "/",
    element: <VisitorHomePage />,
    children: [
      { index: true, element: <Home /> },
      { path: "store/", element: <Store /> },
      { path: "store/:categorySlug/", element: <Store /> },
      { path: "products/:productSlug/", element: <ProductDetail /> },
      { path: "cart/", element: <Cart /> },
      { path: "login/", element: <LoginAndSignup /> },
      { path: "about/", element: <About /> },

      // ✅ Now Checkout + Orders under VisitorHomePage (so Navbar shows)
      {
        element: <ProtectedRoutes />, // requires login
        children: [
          { path: "checkout/", element: <Checkout /> },
          { path: "orders/", element: <OrderList /> },
          { path: "orders/:id/", element: <OrderDetail /> },
        ],
      },
    ],
  },

  // Password & activation routes
  {
    element: (
      <ProtectedRoutes
        allowedRoles={["customer", "admin", "investor", "promoter"]}
      />
    ),
    children: [{ path: "/change-password", element: <ChangePassword /> }],
  },
  {path:"forgot-password/",element:<ForgotPassword/>},
  { path: "/reset-password-confirm/:uid/:token", element: <ConfirmResetPassword/> },
  { path: "/activate/:uid/:token", element: <ActivateAccount /> },
  { path: "/verify-email", element: <VerifyEmail /> },
  { path: "/auth/facebook", element: <FacebookAuth /> },
  { path: "/auth/google", element: <GoogleAuth /> },

  // Dashboards (separate, no Navbar)
  {
    element: <ProtectedRoutes allowedRoles={["customer"]} />,
    children: [{ path: "/customer", element: <CustomerDashboard /> }],
  },
  {
    element: <ProtectedRoutes allowedRoles={["admin"]} />,
    children: [{ path: "/admin", element: <AdminDashboard /> }],
  },
  {
    element: <ProtectedRoutes allowedRoles={["investor"]} />,
    children: [{ path: "/investor", element: <InvestorDashboard /> }],
  },
  {
    element: <ProtectedRoutes allowedRoles={["promoter"]} />,
    children: [{ path: "/promoter", element: <PromoterDashboard /> }],
  },
  {
    element: <ProtectedRoutes allowedRoles={["warehouse_staff"]} />,
    children: [{ path: "/warehouse", element: <WarehouseDashboard /> }],
  },
  {
    element: <ProtectedRoutes allowedRoles={["deliveryman"]} />,
    children: [{ path: "/delivery", element: <DeliveryManDashboard /> }],
  },

  // Fallback
  { path: "*", element: <VisitorHomePage /> },
]);
