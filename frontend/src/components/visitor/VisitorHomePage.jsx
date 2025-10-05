import React,{useState,useEffect} from "react";
import Navbar from "./Navbar";
import { Outlet } from "react-router-dom";
import { useAuth } from "../../contexts/authContext";
import BottomNav from "./MobileBottomNav";
import { useCartCount } from "../../utils/useCartCount";


const VisitorHomePage = () => {
  const { isAuthenticated, logout } = useAuth();
  const totalItems = useCartCount();
  return (
    <div className="min-h-screen flex flex-col">
          <div className="fixed top-0 left-0 w-full z-50 bg-white shadow">
      <Navbar
        isAuthenticated={isAuthenticated}
        totalItems={totalItems}
        logout={logout}
      />
    </div>


      <div className="pt-[64px] px-4">
        <Outlet />
      </div>

      <BottomNav
        isAuthenticated={isAuthenticated}
        totalItems={totalItems}
        logout={logout}
      />
    </div>
  );
};

export default VisitorHomePage;
