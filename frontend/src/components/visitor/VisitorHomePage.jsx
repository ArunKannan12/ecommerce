import React from "react";
import Navbar from "./Navbar";
import { Outlet, useLocation } from "react-router-dom";

const VisitorHomePage = () => {
  const location = useLocation();

  // Check if route is home
  const isHome = location.pathname === "/";

  return (
    <div className="min-h-screen flex flex-col">
      {/* Fixed Navbar */}
      <div className="fixed top-0 left-0 w-full z-50 bg-white shadow">
        <Navbar />
      </div>

      {/* Add padding to prevent content hiding under navbar */}
      <div className="pt-[64px] flex-1">
        {isHome ? (
          <main className="w-full py-8">
            <Outlet />
          </main>
        ) : (
          <main className="w-full py-8">
            <Outlet />
          </main>
        )}
      </div>
    </div>
  );
};

export default VisitorHomePage;
