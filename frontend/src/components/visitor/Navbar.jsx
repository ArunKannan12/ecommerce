import React, { useState, useEffect, useRef } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Menu, X, ChevronDown, User } from "lucide-react";
import { useGetCartQuery } from "../../contexts/cartSlice";
import { useAuth } from "../../contexts/AuthContext";
import MobileMenu from "./MobileMenu";

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [guestCount, setGuestCount] = useState(0);
  const debounceTimeout = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, logout } = useAuth();

  const { data: cartData } = useGetCartQuery(undefined, {
    skip: !isAuthenticated,
    refetchOnMountOrArgChange: true,
  });

  const authCartCount = isAuthenticated
    ? cartData?.reduce((sum, item) => sum + (item.quantity || 0), 0)
    : 0;

  useEffect(() => {
    if (!isAuthenticated) {
      const updateGuestCount = () => {
        const cart = JSON.parse(localStorage.getItem("cart")) || [];
        const total = cart.reduce((sum, item) => sum + (item.quantity || 0), 0);
        setGuestCount(total);
      };
      updateGuestCount();
      window.addEventListener("storage", updateGuestCount);
      window.addEventListener("cartUpdated", updateGuestCount);
      return () => {
        window.removeEventListener("storage", updateGuestCount);
        window.removeEventListener("cartUpdated", updateGuestCount);
      };
    }
  }, [isAuthenticated]);

  const totalItems = isAuthenticated ? authCartCount : guestCount;

  useEffect(() => {
    if (location.pathname.startsWith("/store")) {
      const params = new URLSearchParams(location.search);
      setQuery(params.get("search") || "");
    } else {
      setQuery("");
    }
  }, [location]);

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
    setIsOpen(false);
  };

  return (
    <nav className="fixed top-0 left-0 w-full z-50 bg-white/80 backdrop-blur-md shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto flex items-center justify-between px-4 py-5">
        <Link to="/" className="text-2xl font-bold text-gray-800">MyStore</Link>

        <div className="flex-grow max-w-lg mx-auto px-4">
          <form onSubmit={handleSearchSubmit} className="flex items-center border border-gray-300 rounded-full overflow-hidden shadow-sm focus-within:ring-2 focus-within:ring-blue-500 transition-all">
            <input
              type="search"
              placeholder="Search products..."
              className="px-4 py-2 w-full text-gray-700 placeholder-gray-400 focus:outline-none"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button type="submit" className="bg-blue-600 text-white px-5 py-2 font-semibold hover:bg-blue-700 transition-colors">
              Search
            </button>
          </form>
        </div>

        <div className="flex items-center space-x-6">
          <div className="hidden md:flex items-center space-x-6 text-gray-800 font-medium">
            <Link to="/">Home</Link>
            <Link to="/store">Products</Link>
            <Link to="/cart" className="relative">
              Cart
              {totalItems > 0 && (
                <span className="ml-2 inline-block bg-red-600 text-white rounded-full px-2 text-xs font-semibold">
                  {totalItems}
                </span>
              )}
            </Link>

            {isAuthenticated && (
              <div className="relative group">
                <button className="flex items-center space-x-2 hover:text-blue-600">
                  <User size={18} />
                  <span>Account</span>
                  <ChevronDown size={16} />
                </button>
                <div className="absolute right-0 mt-2 w-44 bg-white border rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50">
                  <Link to="/profile" className="block px-4 py-2 hover:bg-gray-100">Profile</Link>
                  <Link to="/orders" className="block px-4 py-2 hover:bg-gray-100">Orders</Link>
                  <button
                    onClick={logout}
                    className="w-full text-left px-4 py-2 text-red-600 hover:bg-gray-100"
                  >
                    Logout
                  </button>
                </div>
              </div>
            )}

            {!isAuthenticated && <Link to="/login">Login</Link>}
          </div>

          <button className="md:hidden" onClick={() => setIsOpen(!isOpen)}>
            {isOpen ? <X size={28} /> : <Menu size={28} />}
          </button>
        </div>
      </div>

      <MobileMenu
        isOpen={isOpen}
        setIsOpen={setIsOpen}
        isAuthenticated={isAuthenticated}
        totalItems={totalItems}
        logout={logout}
      />
    </nav>
  );
};

export default Navbar;