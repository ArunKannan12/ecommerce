// src/hooks/useCartCount.js
import { useState, useEffect, useMemo } from "react";
import { useAuth } from "../contexts/authContext";
import { useGetCartQuery } from "../contexts/cartSlice";

export const useCartCount = () => {
  const { isAuthenticated } = useAuth();
  const [guestCount, setGuestCount] = useState(0);

  const { data: cartData } = useGetCartQuery(undefined, {
    skip: !isAuthenticated,
    refetchOnMountOrArgChange: true,
  });

  const authCartCount = useMemo(
    () => (isAuthenticated ? cartData?.reduce((sum, item) => sum + (item.quantity || 0), 0) : 0),
    [cartData, isAuthenticated]
  );

  useEffect(() => {
    const updateGuestCount = () => {
      const cart = JSON.parse(localStorage.getItem("cart")) || [];
      const total = cart.reduce((sum, item) => sum + (item.quantity || 0), 0);
      setGuestCount(total);
    };

    if (!isAuthenticated) {
      updateGuestCount();
    }

    window.addEventListener("storage", updateGuestCount);
    window.addEventListener("cartUpdated", updateGuestCount);

    return () => {
      window.removeEventListener("storage", updateGuestCount);
      window.removeEventListener("cartUpdated", updateGuestCount);
    };
  }, [isAuthenticated]);

  return isAuthenticated ? authCartCount : guestCount;
};
