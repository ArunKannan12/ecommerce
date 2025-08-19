import React from "react";
import { Link } from "react-router-dom";

const MobileMenu = ({ isOpen, setIsOpen, isAuthenticated, totalItems, logout }) => {
  if (!isOpen) return null;

  return (
    <div className="md:hidden fixed top-0 right-0 h-full w-64 bg-white shadow-lg z-50 px-6 py-8 space-y-6 transition-transform duration-300">
      <Link to="/" onClick={() => setIsOpen(false)} className="block text-gray-800 font-medium">Home</Link>
      <Link to="/store" onClick={() => setIsOpen(false)} className="block text-gray-800 font-medium">Products</Link>
      <Link to="/cart" onClick={() => setIsOpen(false)} className="block text-gray-800 font-medium relative">
        Cart
        {totalItems > 0 && (
          <span className="absolute top-0 right-0 bg-red-600 text-white rounded-full px-2 text-xs font-semibold">
            {totalItems}
          </span>
        )}
      </Link>

      {isAuthenticated ? (
        <div className="pt-4 border-t border-gray-300 space-y-2">
          <div className="text-sm uppercase tracking-wide text-gray-500">Account</div>
          <Link to="/profile" onClick={() => setIsOpen(false)} className="block text-gray-800">Profile</Link>
          <Link to="/orders" onClick={() => setIsOpen(false)} className="block text-gray-800">Orders</Link>
          <button
            onClick={() => {
              logout();
              setIsOpen(false);
            }}
            className="block text-left text-red-600 hover:underline"
          >
            Logout
          </button>
        </div>
      ) : (
        <Link to="/login" onClick={() => setIsOpen(false)} className="block text-blue-600 font-semibold">Login</Link>
      )}
    </div>
  );
};

export default MobileMenu;