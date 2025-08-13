import React, { useState, useEffect, useRef } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { useGetCartQuery } from "../../contexts/cartSlice";
import { useAuth } from "../../contexts/AuthContext";

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [guestCount, setGuestCount] = useState(0);
  const navigate = useNavigate();
  const location = useLocation();
  const debounceTimeout = useRef(null);

  const { isAuthenticated } = useAuth();

  // Authenticated cart
  const { data: cartData } = useGetCartQuery(undefined, { skip: !isAuthenticated });

  const authCartCount = isAuthenticated
    ? (cartData?.items || []).reduce((sum, item) => sum + (item.quantity || 0), 0)
    : 0;

  // Guest cart: read localStorage & listen for updates
  useEffect(() => {
    if (isAuthenticated) return;

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
  }, [isAuthenticated]);

  const totalItems = isAuthenticated ? authCartCount : guestCount;

  // Sync search query with URL
  useEffect(() => {
    if (location.pathname.startsWith("/store")) {
      const params = new URLSearchParams(location.search);
      setQuery(params.get("search") || "");
    } else {
      setQuery("");
    }
  }, [location]);

  // Debounce search
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
    <nav className="fixed top-0 left-0 w-full z-50 bg-transparent backdrop-blur-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between px-4 py-7">
        {/* Logo */}
        <div className="flex-shrink-0">
          <Link to="/" className="text-2xl font-bold text-dark">MyStore</Link>
        </div>

        {/* Search */}
        <div className="flex-grow max-w-lg mx-auto px-4">
          <form onSubmit={handleSearchSubmit} className="flex items-center border border-gray-300 rounded-lg overflow-hidden shadow-sm focus-within:shadow-lg">
            <input
              type="search"
              placeholder="Search products..."
              className="px-4 py-3 w-full text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button type="submit" className="bg-blue-600 text-white px-5 py-3 font-semibold hover:bg-blue-700">
              Search
            </button>
          </form>
        </div>

        {/* Links */}
        <div className="flex items-center space-x-6">
          <div className="hidden md:flex items-center space-x-6">
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
            <Link to="/about">About</Link>
          </div>

          {/* Mobile toggle */}
          <button className="md:hidden" onClick={() => setIsOpen(!isOpen)}>
            {isOpen ? <X size={28} /> : <Menu size={28} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden bg-black/80 px-4 pb-4 space-y-4">
          <Link to="/" onClick={() => setIsOpen(false)}>Home</Link>
          <Link to="/store" onClick={() => setIsOpen(false)}>Products</Link>
          <Link to="/cart" onClick={() => setIsOpen(false)}>
            Cart
            {totalItems > 0 && (
              <span className="ml-2 inline-block bg-red-600 text-white rounded-full px-2 text-xs font-semibold">
                {totalItems}
              </span>
            )}
          </Link>
          <Link to="/about" onClick={() => setIsOpen(false)}>About</Link>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
