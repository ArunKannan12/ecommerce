import React, { useEffect, useState } from "react";
import { toast } from "react-toastify";
import CartShimmer from "../../shimmer/CartShimmer";
import { useAuth } from "../../contexts/AuthContext";
import axiosInstance from "../../api/axiosinstance";
import {
  useGetCartQuery,
  useUpdateCartItemMutation,
  useRemoveCartItemMutation,
} from "../../contexts/cartSlice";

const Cart = () => {
  const { isAuthenticated } = useAuth();

  // Guest cart
  const [guestCartItems, setGuestCartItems] = useState([]);
  const [guestLoading, setGuestLoading] = useState(false);

  // Auth cart
  const {
    data: authCartData,
    isLoading: authLoading,
    refetch: refetchCart,
  } = useGetCartQuery(undefined, { skip: !isAuthenticated });

  const [updateCartItem] = useUpdateCartItemMutation();
  const [removeCartItem] = useRemoveCartItemMutation();

  // Fetch guest cart details
  useEffect(() => {
    if (isAuthenticated) return;

    const fetchGuestCart = async () => {
      setGuestLoading(true);
      const localCart = JSON.parse(localStorage.getItem("cart")) || [];

      if (!localCart.length) {
        setGuestCartItems([]);
        setGuestLoading(false);
        return;
      }

      const variantIds = localCart.map((item) => item.product_variant_id);
      try {
        const res = await axiosInstance.post("product-variants/bulk/", {
          variant_ids: variantIds,
        });

        const enriched = res.data.map((variant) => {
          const localItem = localCart.find(
            (i) => i.product_variant_id === variant.id
          );
          return { ...variant, quantity: localItem?.quantity || 1 };
        });

        setGuestCartItems(enriched);
      } catch {
        toast.error("Failed to load product details");
        setGuestCartItems(localCart);
      }
      setGuestLoading(false);
    };

    fetchGuestCart();
  }, [isAuthenticated]);

  const cartItems = isAuthenticated
    ? authCartData?.items || []
    : guestCartItems;

  const loading = isAuthenticated ? authLoading : guestLoading;

  // Update quantity
  const handleUpdateQuantity = (variantId, newQty) => {
    if (newQty < 1) return;

    if (isAuthenticated) {
      const cartItem = cartItems.find((i) => i.product_variant.id === variantId);
      if (!cartItem) return;
      updateCartItem({ id: cartItem.id, quantity: newQty }).unwrap()
        .catch(() => toast.error("Failed to update quantity"));
    } else {
      setGuestCartItems((prev) => {
        const updated = prev.map((item) =>
          item.id === variantId ? { ...item, quantity: newQty } : item
        );
        localStorage.setItem(
          "cart",
          JSON.stringify(
            updated.map((i) => ({ product_variant_id: i.id, quantity: i.quantity }))
          )
        );
       setTimeout(() => window.dispatchEvent(new Event("cartUpdated")), 0);
        return updated;
      });
    }
  };

  // Remove item
  const handleRemoveItem = (variantId) => {
    if (isAuthenticated) {
      const cartItem = cartItems.find((i) => i.product_variant.id === variantId);
      if (!cartItem) return;
      removeCartItem(cartItem.id).unwrap()
        .then(() => refetchCart())
        .catch(() => toast.error("Failed to remove item"));
    } else {
      setGuestCartItems((prev) => {
        const updated = prev.filter((i) => i.id !== variantId);
        localStorage.setItem(
          "cart",
          JSON.stringify(
            updated.map((i) => ({ product_variant_id: i.id, quantity: i.quantity }))
          )
        );
       setTimeout(() => window.dispatchEvent(new Event("cartUpdated")), 0);
        return updated;
      });
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">Your Cart</h1>
      <div className="space-y-6">
        {loading ? (
          <CartShimmer count={3} />
        ) : !cartItems.length ? (
          <p className="text-center text-gray-500">No cart items found</p>
        ) : (
          <>
            {cartItems.map((item) => {
              const variant = isAuthenticated ? item.product_variant : item;
              return (
                <div key={variant.id} className="flex items-center border rounded-lg p-5 shadow-sm">
                  <img src={variant.images?.[0]?.image_url || "/placeholder.png"} alt={variant.variant_name} className="w-14 h-14 object-cover rounded-md mr-6" />
                  <div className="flex-1">
                    <p className="font-semibold text-xl">{variant.variant_name}</p>
                    <p className="text-gray-900 font-semibold mt-2">Price: ₹{variant.price}</p>
                    <p className="text-gray-900 font-semibold mt-1">Subtotal: ₹{(item.quantity * variant.price).toFixed(2)}</p>
                  </div>
                  <div className="flex items-center space-x-3">
                    <button onClick={() => handleUpdateQuantity(variant.id, item.quantity - 1)} disabled={item.quantity <= 1} className="px-3 py-1 border rounded-md">-</button>
                    <span className="text-lg font-medium">{item.quantity}</span>
                    <button onClick={() => handleUpdateQuantity(variant.id, item.quantity + 1)} className="px-3 py-1 border rounded-md">+</button>
                  </div>
                  <button onClick={() => handleRemoveItem(variant.id)} className="ml-6 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition">Remove</button>
                </div>
              );
            })}
          </>
        )}
      </div>
    </div>
  );
};

export default Cart;
