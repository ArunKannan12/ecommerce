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
import { useNavigate } from "react-router-dom";

const Cart = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [guestCartItems, setGuestCartItems] = useState([]);

  // RTK Query for authenticated cart
  const {
    data: authCartData,
    isLoading: authLoading,
    refetch: refetchCart,
  } = useGetCartQuery(undefined, { skip: !isAuthenticated });

  const [updateCartItem] = useUpdateCartItemMutation();
  const [removeCartItem] = useRemoveCartItemMutation();

  // Fetch guest cart from localStorage
  const loadGuestCart = async () => {
    const localCart = JSON.parse(localStorage.getItem("cart")) || [];
    if (!localCart.length) {
      setGuestCartItems([]);
      return;
    }

    try {
      const variantIds = localCart.map((item) => item.product_variant_id);
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
  };

  // Initial load for guest cart
  useEffect(() => {
    if (!isAuthenticated) {
      loadGuestCart();
    }
  }, [isAuthenticated]);

  // Listen for guest cart updates
  useEffect(() => {
    if (!isAuthenticated) {
      const handleCartUpdate = () => loadGuestCart();
      window.addEventListener("cartUpdated", handleCartUpdate);
      return () => window.removeEventListener("cartUpdated", handleCartUpdate);
    }
  }, [isAuthenticated]);

  const cartItems = isAuthenticated ? authCartData || [] : guestCartItems;
  const loading = isAuthenticated ? authLoading : false;

  const handleUpdateQuantity = (variantId, newQty) => {
    if (newQty < 1) return;

    if (isAuthenticated) {
      const cartItem = cartItems.find(
        (i) => i.product_variant_detail.id === variantId
      );
      if (!cartItem) return;

      // Optimistic UI update
      const updated = cartItems.map((item) =>
        item.product_variant_detail.id === variantId
          ? { ...item, quantity: newQty }
          : item
      );

      // No setState — RTK Query handles state sync after mutation
      updateCartItem({ id: cartItem.id, quantity: newQty }).unwrap().catch(() => {
        toast.error("Failed to update quantity");
        refetchCart(); // rollback
      });

    } else {
      const updated = guestCartItems.map((item) =>
        item.id === variantId ? { ...item, quantity: newQty } : item
      );
      localStorage.setItem(
        "cart",
        JSON.stringify(
          updated.map((i) => ({
            product_variant_id: i.id,
            quantity: i.quantity,
          }))
        )
      );
      setGuestCartItems(updated);
      window.dispatchEvent(new Event("cartUpdated"));
    }
  };

  const handleRemoveItem = (variantId) => {
    if (isAuthenticated) {
      const cartItem = cartItems.find(
        (i) => i.product_variant_detail.id === variantId
      );
      if (!cartItem) return;

      removeCartItem(cartItem.id).unwrap().catch(() => {
        toast.error("Failed to remove item");
      });

    } else {
      const updated = guestCartItems.filter((i) => i.id !== variantId);
      localStorage.setItem(
        "cart",
        JSON.stringify(
          updated.map((i) => ({
            product_variant_id: i.id,
            quantity: i.quantity,
          }))
        )
      );
      setGuestCartItems(updated);
      window.dispatchEvent(new Event("cartUpdated"));
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
              const variant = isAuthenticated
                ? item.product_variant_detail
                : item;
              const imageUrl =
                variant.images?.[0]?.image_url ||
                (variant.product_images?.[0] &&
                  `http://localhost:8000${variant.product_images[0]}`) ||
                "/placeholder.png";

              return (
                <div
                  key={variant.id}
                  className="flex flex-col md:flex-row items-start md:items-center border rounded-lg p-5 shadow-sm"
                >
                  <img
                    src={imageUrl}
                    alt={variant.product_name}
                    className="w-20 h-20 object-cover rounded-md mb-4 md:mb-0 md:mr-6"
                  />
                  <div className="flex-1">
                    <h2 className="text-lg font-semibold">
                      {variant.product_name} - {variant.variant_name}
                    </h2>
                    <p className="text-sm text-gray-500">
                      {variant.product_description}
                    </p>
                    <p className="mt-2 font-medium text-gray-800">
                      Price: ₹{variant.price}
                    </p>
                    <p className="text-sm text-gray-600">
                      Subtotal: ₹{(variant.price * item.quantity).toFixed(2)}
                    </p>
                    {variant.stock < 5 && (
                      <p className="text-red-600 text-sm mt-1">
                        Only {variant.stock} left in stock!
                      </p>
                    )}
                  </div>
                  <div className="flex items-center space-x-2 mt-4 md:mt-0">
                    <button
                      onClick={() =>
                        handleUpdateQuantity(variant.id, item.quantity - 1)
                      }
                      disabled={item.quantity <= 1}
                      className="px-2 py-1 border rounded"
                    >
                      -
                    </button>
                    <span>{item.quantity}</span>
                    <button
                      onClick={() =>
                        handleUpdateQuantity(variant.id, item.quantity + 1)
                      }
                      disabled={item.quantity >= variant.stock}
                      className="px-2 py-1 border rounded"
                    >
                      +
                    </button>
                  </div>
                  <button
                    onClick={() => handleRemoveItem(variant.id)}
                    className="ml-4 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                  >
                    Remove
                  </button>
                </div>
              );
            })}

            <div className="mt-8 border-t pt-6 flex justify-between items-center">
              <p className="text-xl font-bold">
                Total: ₹
                {cartItems
                  .reduce((acc, item) => {
                    const variant = isAuthenticated
                      ? item.product_variant_detail
                      : item;
                    return acc + variant.price * item.quantity;
                  }, 0)
                  .toFixed(2)}
              </p>
              <button
                onClick={() => {
                  if (isAuthenticated) {
                    navigate("/checkout");
                  } else {
                    toast.info("Please log in as a customer to proceed to checkout");
                    navigate("/login", { state: { from: "/checkout" } });
                  }
                }}

                className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition"
              >
                Proceed to Checkout
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Cart;
