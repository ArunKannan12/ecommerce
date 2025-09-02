// router.js
import React, { Suspense, lazy } from "react";
import { createBrowserRouter } from "react-router-dom";
import ProtectedRoutes from "./ProtectedRoutes";
import LoadingScreen from "../components/helpers/LoadinScreen";

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

const CustomerDashboard = lazy(() => import("../components/customer/CustomerDashboard"));
const AdminDashboard=lazy(()=>import("../components/admin/AdminDashboard") )
const InvestorDashboard = lazy(() => import("../components/investor/InvestorDashboard"));
const PromoterDashboard = lazy(() => import("../components/promoter/PromoterDashboard"));
const WarehouseDashboard = lazy(() => import("../components/warehousestaff/WarehouseDashboard"));
const DeliveryManDashboard = lazy(() => import("../components/deliveryman/DeliveryManDashboard"));

const ChangePassword = lazy(() => import("../components/visitor/ChangePassword"));
const FacebookAuth = lazy(() => import("../components/visitor/FacebookAuth"));
const GoogleAuth = lazy(() => import("../components/visitor/GoogleAuth"));
const ActivateAccount = lazy(() => import("../components/visitor/ActivateAccount"));
const VerifyEmail = lazy(() => import("../components/visitor/VerifyEmail"));
const ForgotPassword = lazy(() => import("../components/visitor/ForgotPassword"));
const ConfirmResetPassword = lazy(() => import("../components/visitor/ConfirmResetPassword"));
const Profile = lazy(() => import("../components/visitor/Profile"));

// 🌀 Suspense wrapper
const withSuspense = (Component) => (
  <Suspense fallback={<LoadingScreen/>}>
    {Component}
  </Suspense>
);

// 🚀 Router setup
export const router = createBrowserRouter([
  {
    path: "/",
    element: withSuspense(<VisitorHomePage />),
    children: [
      { index: true, element: withSuspense(<Home />) },
      { path: "store/", element: withSuspense(<Store />) },
      { path: "store/:categorySlug/", element: withSuspense(<Store />) },
      { path: "products/:productSlug/", element: withSuspense(<ProductDetail />) },
      { path: "cart/", element: withSuspense(<Cart />) },
      { path: "login/", element: withSuspense(<LoginAndSignup />) },
      { path: "about/", element: withSuspense(<About />) },

      {
        element: <ProtectedRoutes />,
        children: [
          { path: "profile/", element: withSuspense(<Profile />) },
          { path: "checkout/", element: withSuspense(<Checkout />) },
          { path: "orders/", element: withSuspense(<OrderList />) },
          { path: "orders/:id/", element: withSuspense(<OrderDetail />) },
        ],
      },
    ],
  },

  {
    element: <ProtectedRoutes allowedRoles={["customer", "admin", "investor", "promoter", "warehouse_staff", "deliveryman"]} />,
    children: [
      { path: "/profile", element: withSuspense(<Profile />) },
      { path: "/change-password", element: withSuspense(<ChangePassword />) },
    ],
  },

  { path: "forgot-password/", element: withSuspense(<ForgotPassword />) },
  { path: "/reset-password-confirm/:uid/:token", element: withSuspense(<ConfirmResetPassword />) },
  { path: "/activation/:uid/:token", element: withSuspense(<ActivateAccount />) },
  { path: "/verify-email", element: withSuspense(<VerifyEmail />) },
  { path: "/auth/facebook", element: withSuspense(<FacebookAuth />) },
  { path: "/auth/google", element: withSuspense(<GoogleAuth />) },

  {
    element: <ProtectedRoutes allowedRoles={["customer"]} />,
    children: [{ path: "/customer", element: withSuspense(<CustomerDashboard />) }],
  },
  {
    element: <ProtectedRoutes allowedRoles={["admin"]} />,
    children: [{ path: "/admin", element: withSuspense(<AdminDashboard />) }],
  },
  {
    element: <ProtectedRoutes allowedRoles={["investor"]} />,
    children: [{ path: "/investor", element: withSuspense(<InvestorDashboard />) }],
  },
  {
    element: <ProtectedRoutes allowedRoles={["promoter"]} />,
    children: [{ path: "/promoter", element: withSuspense(<PromoterDashboard />) }],
  },
  {
    element: <ProtectedRoutes allowedRoles={["warehouse_staff"]} />,
    children: [{ path: "/warehouse", element: withSuspense(<WarehouseDashboard />) }],
  },
  {
    element: <ProtectedRoutes allowedRoles={["deliveryman"]} />,
    children: [{ path: "/delivery", element: withSuspense(<DeliveryManDashboard />) }],
  },

  { path: "*", element: withSuspense(<VisitorHomePage />) },
]);