// components/admin/AdminDashboard.jsx
import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../../contexts/authContext";
import Sidebars from "./helpers/Sidebars";
import {
  LayoutDashboard,
  Package,
  Users,
  ShoppingCart,
  Warehouse,
  Truck,
  Image as BannerIcon,
} from "lucide-react";

const adminSections = [
  { label: "Dashboard", to: "/admin/dashboard", icon: LayoutDashboard },
  {
    label: "Products",
    icon: Package,
    subLinks: [
      { name: "All Products", to: "/admin/products" },
      { name: "Categories", to: "/admin/categories" },
    ],
  },
  {
    label: "Customers",
    icon: Users,
    subLinks: [
      { name: "All Customers", to: "/admin/customers" },
      { name: "Wallets", to: "/admin/wallets" },
    ],
  },
  {
    label: "Orders",
    icon: ShoppingCart,
    subLinks: [
      { name: "All Orders", to: "/admin/orders" },
      { name: "Returns/Replacement", to: "/admin/returns" },
    ],
  },
  {
    label: "Warehouse",
    icon: Warehouse,
    subLinks: [
      { name: "Stock", to: "/admin/warehouse/stock" },
      { name: "Suppliers", to: "/admin/warehouse/suppliers" },
    ],
  },
  {
    label: "Delivery",
    icon: Truck,
    subLinks: [
      { name: "Staff", to: "/admin/delivery/staff" },
      { name: "Assign Orders", to: "/admin/delivery/assign" },
    ],
  },
  { label: "Banners", to: "/admin/banners", icon: BannerIcon },
];

const AdminDashboard = () => {
  const { logout, user } = useAuth();

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-md flex flex-col">
        <div className="p-6 text-center border-b">
          <h1 className="text-xl font-bold">Admin Panel</h1>
          <p className="text-sm text-gray-500">{user?.email}</p>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          {adminSections.map((section) =>
            section.subLinks ? (
              <Sidebars
                key={section.label}
                label={section.label}
                subLinks={section.subLinks}
                icon={section.icon}
              />
            ) : (
              <NavLink
                key={section.label}
                to={section.to}
                className={({ isActive }) =>
                  `flex items-center gap-2 p-2 rounded ${
                    isActive ? "bg-blue-500 text-white" : "text-gray-700"
                  }`
                }
              >
                {section.icon && <section.icon className="w-5 h-5" />}
                <span>{section.label}</span>
              </NavLink>
            )
          )}
        </nav>

        <div className="p-4 border-t">
          <button
            onClick={logout}
            className="w-full py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
};

export default AdminDashboard;
