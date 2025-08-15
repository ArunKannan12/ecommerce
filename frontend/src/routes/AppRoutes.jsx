import { createBrowserRouter } from "react-router-dom";
import About from "../components/visitor/About";
import Cart from "../components/visitor/Cart";
import Checkout from "../components/visitor/Checkout";
import Home from "../components/visitor/Home";
import LoginAndSignup from "../components/visitor/LoginAndSignup";
import ProductDetail from "../components/visitor/ProductDetail";
import Store from "../components/visitor/Store";
import VisitorHomePage from "../components/visitor/VisitorHomePage";
import ProtectedRoutes from "./ProtectedRoutes";
import CustomerDashboard from "../components/customer/CustomerDashboard";
import AdminDashboard from "../components/admindashboard/AdminDashboard";
import InvestorDashboard from "../components/investor/InvestorDashboard";
import PromoterDashboard from "../components/promoter/PromoterDashboard";
import WarehouseDashboard from "../components/warehousestaff/WarehouseDashboard";
import DeliveryManDashboard from "../components/deliveryman/DeliveryManDashboard";
import OrderList from "../components/visitor/OrderList";
import OrderDetail from "../components/visitor/OrderDetail";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <VisitorHomePage />,
    children: [
      { index: true, element: <Home /> },
      { path: "store/", element: <Store /> },
      { path: "store/:categorySlug/", element: <Store /> },
      { path: "products/:productSlug/", element: <ProductDetail /> },
      { path: "cart/", element: <Cart /> },
      { path: "orders/", element: <OrderList /> },
      { path: "orders/:id/", element: <OrderDetail /> },
      
      {
        path: "checkout/",
        element: (
          
            <Checkout />
         
        ),
      },
      // {
      //   path: "orders/",
      //   element: (
      //     <ProtectedRoutes allowedRoles={["customer"]}>
      //       <OrderList /> 
      //     </ProtectedRoutes>
      //   ),
      // },
      // {
      //   path: "orders/:id/",
      //   element: (
      //     <ProtectedRoutes allowedRoles={["customer"]}>
      //       <OrderDetail /> 
      //     </ProtectedRoutes>
      //   ),
      // },

      { path: "login/", element: <LoginAndSignup /> },
      { path: "about/", element: <About /> },
    ],
  },

  // Customer dashboard
  {
    element: <ProtectedRoutes allowedRoles={["customer"]} />,
    children: [
      { path: "/customer", element: <CustomerDashboard /> },
    ],
  },

  // Admin dashboard
  {
    element: <ProtectedRoutes allowedRoles={["admin"]} />,
    children: [
      { path: "/admin", element: <AdminDashboard /> },
    ],
  },

  // Investor dashboard
  {
    element: <ProtectedRoutes allowedRoles={["investor"]} />,
    children: [
      { path: "/investor", element: <InvestorDashboard /> },
    ],
  },

  // Promoter dashboard
  {
    element: <ProtectedRoutes allowedRoles={["promoter"]} />,
    children: [
      { path: "/promoter", element: <PromoterDashboard /> },
    ],
  },

  // Warehouse Staff dashboard
  {
    element: <ProtectedRoutes allowedRoles={["warehouse_staff"]} />,
    children: [
      { path: "/warehouse", element: <WarehouseDashboard /> },
    ],
  },

  // Delivery dashboard
  {
    element: <ProtectedRoutes allowedRoles={["deliveryman"]} />,
    children: [
      { path: "/delivery", element: <DeliveryManDashboard /> },
    ],
  },
]);
