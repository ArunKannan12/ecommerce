import React, { useEffect, useState } from "react";
import { toast } from "react-toastify";
import CartShimmer from "../../shimmer/CartShimmer";
import axiosInstance from "../../api/axiosinstance";
import {
  useGetCartQuery,
  useUpdateCartItemMutation,
  useRemoveCartItemMutation,
} from "../../contexts/cartSlice";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/authContext";

const Cart = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [guestCartItems, setGuestCartItems] = useState([]);

  const { data: authCartData, isLoading: authLoading, refetch: refetchCart } =
    useGetCartQuery(undefined, { skip: !isAuthenticated });

  const [updateCartItem] = useUpdateCartItemMutation();
  const [removeCartItem] = useRemoveCartItemMutation();

  // Load guest cart
  const loadGuestCart = async () => {
    const localCart = JSON.parse(localStorage.getItem("cart")) || [];
    if (!localCart.length) return setGuestCartItems([]);

    try {
      const variantIds = localCart.map((item) => item.product_variant_id);
      const res = await axiosInstance.post("product-variants/bulk/", {
        variant_ids: variantIds,
      });

      const enriched = res.data.map((variant) => {
        const localItem = localCart.find(
          (i) => i.product_variant_id === variant.id
        );

        const final_price =
          variant.offer_price && parseFloat(variant.offer_price) < parseFloat(variant.base_price)
            ? parseFloat(variant.offer_price)
            : parseFloat(variant.base_price);

        return {
          ...variant,
          quantity: localItem?.quantity || 1,
          final_price,
        };
      });

      setGuestCartItems(enriched);
    } catch {
      toast.error("Failed to load product details");
      setGuestCartItems(localCart);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) loadGuestCart();
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) {
      const handleCartUpdate = () => loadGuestCart();
      window.addEventListener("cartUpdated", handleCartUpdate);
      return () => window.removeEventListener("cartUpdated", handleCartUpdate);
    }
  }, [isAuthenticated]);

  const cartItems = isAuthenticated ? authCartData || [] : guestCartItems;
  const loading = isAuthenticated ? authLoading : false;

  const getImageUrl = (item) => {
    if (!item?.images?.length) return "/placeholder.png";
    return item.images[0].url;
  };

  
  

  const handleUpdateQuantity = (itemId, newQty) => {
    if (newQty < 1) return;

    if (isAuthenticated) {
      const cartItem = cartItems.find((i) => i.id === itemId);
      if (!cartItem) return;

      updateCartItem({ id: cartItem.id, quantity: newQty }).catch(() => {
        toast.error("Failed to update quantity");
        refetchCart();
      });
    } else {
      const updated = guestCartItems.map((item) =>
        item.id === itemId ? { ...item, quantity: newQty } : item
      );
      localStorage.setItem(
        "cart",
        JSON.stringify(
          updated.map((i) => ({ product_variant_id: i.id, quantity: i.quantity }))
        )
      );
      setGuestCartItems(updated);
      window.dispatchEvent(new Event("cartUpdated"));
    }
  };

  const handleRemoveItem = (itemId) => {
    if (isAuthenticated) {
      const cartItem = cartItems.find((i) => i.id === itemId);
      if (!cartItem) return;

      removeCartItem(cartItem.id).catch(() => toast.error("Failed to remove item"));
    } else {
      const updated = guestCartItems.filter((i) => i.id !== itemId);
      localStorage.setItem(
        "cart",
        JSON.stringify(
          updated.map((i) => ({ product_variant_id: i.id, quantity: i.quantity }))
        )
      );
      setGuestCartItems(updated);
      window.dispatchEvent(new Event("cartUpdated"));
    }
  };

  const cartTotal = cartItems.reduce(
    (acc, item) => acc + (parseFloat(item.final_price) || 0) * item.quantity,
    0
  );

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-4xl font-extrabold mb-10 text-gray-900">Your Cart</h1>

      {loading ? (
        <CartShimmer count={3} />
      ) : !cartItems.length ? (
        <p className="text-center text-gray-500 text-lg">No items in your cart</p>
      ) : (
        <div className="space-y-8">
          {
          

          
          cartItems.map((item) => (
            <div
              key={item.id}
              className="flex flex-col md:flex-row items-start md:items-center border rounded-xl p-6 shadow-lg hover:shadow-2xl transition-shadow bg-white"
            >
              {/* Product Image */}
              <img
                src={getImageUrl(item)}
                alt={item.product_name || "Product"}
                className="w-28 h-28 object-cover rounded-lg mb-4 md:mb-0 md:mr-6"
              />

              {/* Product Info */}
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-gray-800">
                  {item.product_name} - {item.variant_name || "Default"}
                </h2>
                <p className="text-gray-500 mt-1 line-clamp-2">
                  {item.product_description || "No description available"}
                </p>

                {/* Pricing */}
                <div className="mt-3 flex items-center space-x-4">
                  {item.offer_price && parseFloat(item.offer_price) < parseFloat(item.base_price) ? (
                    <>
                      <p className="text-2xl font-bold text-green-600">
                        ₹{item.final_price}
                      </p>
                      <p className="text-gray-400 line-through">₹{item.base_price}</p>
                      <p className="text-red-500 font-medium">
                        {Math.round(
                          ((item.base_price - item.final_price) / item.base_price) * 100
                        )}
                        % OFF
                      </p>
                    </>
                  ) : (
                    <p className="text-2xl font-bold text-gray-800">₹{item.final_price}</p>
                  )}
                </div>

                {/* Subtotal */}
                <p className="text-gray-600 mt-1">
                  Subtotal: ₹{(item.final_price * item.quantity).toFixed(2)}
                </p>

                {/* Stock Warning */}
                {item.stock < 5 && (
                  <p className="text-red-600 mt-1 font-medium">
                    Only {item.stock} left in stock!
                  </p>
                )}
              </div>

              {/* Quantity Controls */}
              <div className="flex flex-col md:flex-row items-center mt-5 md:mt-0 md:space-x-4 space-y-2 md:space-y-0">
                <div className="flex items-center space-x-2 border rounded-lg px-2 py-1 bg-gray-50">
                  <button
                    onClick={() => handleUpdateQuantity(item.id, item.quantity - 1)}
                    disabled={item.quantity <= 1}
                    className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 transition"
                  >
                    -
                  </button>
                  <span className="font-medium">{item.quantity}</span>
                  <button
                    onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}
                    disabled={item.quantity >= item.stock}
                    className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 transition"
                  >
                    +
                  </button>
                </div>
                <button
                  onClick={() => handleRemoveItem(item.id)}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}

          {/* Cart Total & Checkout */}
          <div className="mt-10 border-t pt-6 flex flex-col md:flex-row justify-between items-center bg-gray-50 p-4 rounded-lg shadow-inner">
            <p className="text-2xl font-bold text-gray-900 mb-4 md:mb-0">
              Total: ₹{cartTotal.toFixed(2)}
            </p>
            <button
              onClick={() => {
                if (isAuthenticated) navigate("/checkout");
                else {
                  toast.info("Please log in as a customer to proceed to checkout");
                  navigate("/login", { state: { from: "/checkout" } });
                }
              }}
              className="px-8 py-3 bg-green-600 text-white text-lg font-semibold rounded-lg hover:bg-green-700 transition"
            >
              Proceed to Checkout
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Cart;
