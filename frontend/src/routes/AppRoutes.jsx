// router.js
import { Suspense, lazy } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import ProtectedRoutes from "./ProtectedRoutes";
import LoadingScreen from "../components/helpers/LoadinScreen";
import { useAuth } from "../contexts/authContext";
const AdminReplacements = lazy(()=>import("../components/admin/pages/AdminReplacements.jsx")) ;
const AdminReturns = lazy(()=>import("../components/admin/pages/AdminReturns.jsx"))
const AdminOrders = lazy(()=> import("../components/admin/pages/AdminOrders.jsx"))
const AdminCustomers = lazy(()=> import("../components/admin/pages/AdminCustomers.jsx"));
const AdminCategories = lazy(() => import ("../components/admin/pages/AdminCategories.jsx"));
const AdminProducts = lazy(()=> import("../components/admin/pages/AdminProducts.jsx"))
const AdminWarehouseLogs = lazy(()=> import ('../components/admin/pages/AdminWarehouseLogs.jsx'))
const AdminDeliveryMan = lazy(()=>import ('../components/admin/pages/AdminDeliveryMan.jsx'))
const AdminAllDeliveryman = lazy(()=>import('../components/admin/pages/AllDeliveryMan.jsx'))
const AdminDeliveryTracking = lazy(()=>import('../components/admin/pages/DeliveryTracking.jsx'))
const AdminAllBanner = lazy(()=>import('../components/admin/pages/AdminAllBanner.jsx'))

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
const ReturnList = lazy(()=>import('../components/visitor/returnReplacement/ReturnList.jsx'))
const ReplacementList = lazy(()=>import('../components/visitor/returnReplacement/ReplacementList.jsx'))

const WarehouseDashboardHome = lazy(()=>import("../components/warehousestaff/pages/WarehouseDashboardHome.jsx")) ;
const WarehouseOrders = lazy(()=>import("../components/warehousestaff/pages/WarehouseOrders.jsx"));
const OrderAssigning = lazy(()=> import ("../components/warehousestaff/pages/OrderAssigning.jsx"))
const WarehouseReturns = lazy(()=>import('../components/warehousestaff/pages/WarehouseReturns.jsx'));
const OrdersToDeliver =lazy(()=>import ("../components/deliveryman/pages/OrdersToDeliver.jsx")) ;
const DeliverymanReturns = lazy(()=>import ("../components/deliveryman/pages/DeliverymanReturns.jsx")) ;
const DeliveryManDashboardHome = lazy(()=>import('../components/deliveryman/pages/DeliveryManDashboardHome.jsx'))

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
      { path: "store", element: withSuspense(<Store />) },
      { path: "store/:categorySlug", element: withSuspense(<Store />) },
      { path: "products/:productSlug", element: withSuspense(<ProductDetail />) },
      { path: "cart", element: withSuspense(<Cart />) },
      { path: "login", element: withSuspense(<LoginAndSignup />) },
      { path: "about", element: withSuspense(<About />) },
      { path: "forgot-password", element: withSuspense(<ForgotPassword />) },
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
        {
          element: withSuspense(<VisitorHomePage />), // Layout wrapper
          children: [
            { path: "/profile", element: withSuspense(<Profile />) },
            { path: "/change-password", element: withSuspense(<ChangePassword />) },
            { path: "/checkout", element: withSuspense(<Checkout />) },
            { path: "/orders/", element: withSuspense(<OrderList />) },
            { path: "/orders/:order_number", element: withSuspense(<OrderDetail />) },
            { path: "/returns", element: withSuspense(<ReturnList />) },
            { path: "replacements", element: withSuspense(<ReplacementList />) },
            { path: "/returns/create/:orderNumber", element: withSuspense(<ReturnRequest />) },
            { path: "/returns/:returnId", element: withSuspense(<ReturnRequest />) },
            { path: "/replacements/create/:orderNumber", element: withSuspense(<ReplacementRequest />) },
          ],
        },
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
        {path:"categories",element:withSuspense(<AdminCategories/>)},
        { path: "customers", element: withSuspense(<AdminCustomers />) },
        {path:"orders",element:withSuspense(<AdminOrders/>)},
        {path:"returns",element:withSuspense(<AdminReturns/>)},
        {path:"replacements",element:withSuspense(<AdminReplacements/>)},
        {path:"warehouse-logs",element:withSuspense(<AdminWarehouseLogs/>)},
        {path:"delivery/delivery-man",element:withSuspense(<AdminDeliveryMan/>)},
        {path:"deliverymen",element:withSuspense(<AdminAllDeliveryman/>)},
        {path:"delivery-tracking",element:withSuspense(<AdminDeliveryTracking/>)},
        {path:'banners',element:withSuspense(<AdminAllBanner/>)},
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
      {
        path: "/warehouse",
        element: withSuspense(<WarehouseDashboard />), // Sidebar + Outlet
        children: [
          
          { index: true, element: <Navigate to="/warehouse/dashboard" replace /> },

          // Warehouse dashboard stats page
          { path: "dashboard", element: withSuspense(<WarehouseDashboardHome />) },
          { path: "orders", element: withSuspense(<WarehouseOrders/>) },
          { path: "order-assigning", element: withSuspense(<OrderAssigning/>) },
          { path: "returns", element: withSuspense(<WarehouseReturns/>) },

        ]
      },
    ],
  },

  // Deliveryman routes
  {
    element: <ProtectedRoutes allowedRoles={["deliveryman"]} />,
    children: [
      { path: "/delivery", 
        element: withSuspense(<DeliveryManDashboard />),
        children:[
          {index:true,element:<Navigate to="dashboard" replace/>},
          {path:'dashboard',element:withSuspense(<DeliveryManDashboardHome/>)},
          {path:'orders-to-deliver',element:withSuspense(<OrdersToDeliver/>)},
          {path:'returns',element:withSuspense(<DeliverymanReturns/>)}
        ]
       },
      { path: "/profile", element: withSuspense(<Profile />) },
      { path: "/change-password", element: withSuspense(<ChangePassword />) },
    ],
  },

  // Fallback
  { path: "*", element: withSuspense(<VisitorHomePage />) },
]);
