import React, { useState, useEffect, useRef } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ChevronDown, User } from "lucide-react";
import { useAuth } from "../../contexts/authContext";
import { useCartCount } from "../../utils/useCartCount";

const Navbar = () => {
  const [query, setQuery] = useState("");
  const debounceTimeout = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, logout } = useAuth();
  const [accountOpen, setAccountOpen] = useState(false);
  const totalItems = useCartCount();

  // Update search query from URL
  useEffect(() => {
    if (location.pathname.startsWith("/store")) {
      const params = new URLSearchParams(location.search);
      setQuery(params.get("search") || "");
    } else {
      setQuery("");
    }
  }, [location]);

  // Debounce search and navigate
  useEffect(() => {
    if (!location.pathname.startsWith("/store")) return;
    const trimmed = query.trim();
    const currentSearch = new URLSearchParams(location.search).get("search") || "";
    if (trimmed === currentSearch) return;

    if (debounceTimeout.current) clearTimeout(debounceTimeout.current);
    debounceTimeout.current = setTimeout(() => {
      navigate(trimmed ? `/store?search=${encodeURIComponent(trimmed)}` : "/store", {
        replace: true,
      });
    }, 500);

    return () => clearTimeout(debounceTimeout.current);
  }, [query, navigate, location.pathname, location.search]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!location.pathname.startsWith("/store")) {
      navigate(trimmed ? `/store?search=${encodeURIComponent(trimmed)}` : "/store");
    }
  };

  return (
    <nav className="fixed top-0 left-0 w-full z-50 bg-white/90 backdrop-blur-md shadow-md border-b border-gray-200 transition-all">
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20 xl:px-32 py-5 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="text-2xl font-bold text-gray-800 hover:text-blue-600 transition-colors">
          Beston
        </Link>

        {/* Search Bar */}
        <div className="flex-grow max-w-lg mx-4">
          <form
            onSubmit={handleSearchSubmit}
            className="flex items-center border border-gray-300 rounded-full overflow-hidden shadow-sm focus-within:ring-2 focus-within:ring-blue-500 transition-all"
          >
            <input
              type="search"
              placeholder="Search products..."
              className="px-4 py-2 w-full text-gray-700 placeholder-gray-400 focus:outline-none transition-all"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button
              type="submit"
              className="bg-blue-600 text-white px-5 py-2 font-semibold hover:bg-blue-700 transition-colors"
            >
              Search
            </button>
          </form>
        </div>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center space-x-6 text-gray-800 font-medium">
          <Link to="/" className="hover:text-blue-600 transition-colors">Home</Link>
          <Link to="/store" className="hover:text-blue-600 transition-colors">Products</Link>
          <Link to="/cart" className="relative hover:text-blue-600 transition-colors">
            Cart
            {totalItems > 0 && (
              <span className="ml-2 inline-block bg-red-600 text-white rounded-full px-2 text-xs font-semibold animate-pulse">
                {totalItems}
              </span>
            )}
          </Link>

          {/* Account Dropdown */}
          {isAuthenticated ? (
            <div className="relative">
              <button
                onClick={() => setAccountOpen((prev) => !prev)}
                className="flex items-center space-x-2 hover:text-blue-600 transition-colors"
              >
                <User size={18} />
                <span>Account</span>
                <ChevronDown
                  size={16}
                  className={`${accountOpen ? "rotate-180" : "rotate-0"} transition-transform duration-300`}
                />
              </button>

              <div
                className={`absolute right-0 mt-2 w-44 bg-white border rounded-md shadow-xl z-50 transform origin-top-right transition-all duration-300 ease-out
                  ${accountOpen ? "opacity-100 scale-100" : "opacity-0 scale-95 pointer-events-none"}
                `}
              >
                <Link
                  to="/profile"
                  className="block px-4 py-2 hover:bg-gray-100 transition-colors"
                  onClick={() => setAccountOpen(false)}
                >
                  Profile
                </Link>
                <Link
                  to="/orders"
                  className="block px-4 py-2 hover:bg-gray-100 transition-colors"
                  onClick={() => setAccountOpen(false)}
                >
                  Orders
                </Link>
                <button
                  onClick={() => {
                    logout();
                    setAccountOpen(false);
                  }}
                  className="w-full text-left px-4 py-2 text-red-600 hover:bg-gray-100 transition-colors"
                >
                  Logout
                </button>
              </div>
            </div>
          ) : (
            <Link to="/login" className="hover:text-blue-600 transition-colors">Login</Link>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
