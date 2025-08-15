import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { useAuth } from "../../contexts/AuthContext";
import axiosInstance from "../../api/axiosinstance";
import { useGetCartQuery } from "../../contexts/cartSlice";

import CartItemList from "./CartItemList";
import ShippingAddressSelector from "./ShippingAddressSelector";
import PaymentMethodSelector from "./PaymentMethodSelector";
import CheckoutSummary from "./CheckoutSummary";
import { handleRazorpayPayment } from "../../utils/payment";

const Checkout = () => {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const buyNowItems = location.state?.buyNowItems || [];

  const { data: authCartData, refetch: refetchCart } = useGetCartQuery(undefined, { skip: !isAuthenticated });

  const [guestCartItems, setGuestCartItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const [shippingAddresses, setShippingAddresses] = useState([]);
  const [selectedAddressId, setSelectedAddressId] = useState(null);
  const [newAddress, setNewAddress] = useState({
    full_name: "",
    phone_number: "",
    address: "",
    city: "",
    postal_code: "",
    country: "",
  });

  const [paymentMethod, setPaymentMethod] = useState("");
  const [pendingOrderId, setPendingOrderId] = useState(null);

  // Helpers
  const getSelectedAddress = () =>
    selectedAddressId
      ? shippingAddresses.find((addr) => addr.id === selectedAddressId)
      : newAddress;

  const getCartItems = () => {
    if (buyNowItems.length) return buyNowItems;
    if (isAuthenticated) return authCartData ?? []; // wait until query resolves
    return guestCartItems;
  };

  const buildItemsPayload = (items) =>
    items.map((item) => ({
      product_variant: isAuthenticated ? item.product_variant_detail.id : item.id,
      quantity: item.quantity,
    }));

  // Load guest cart and saved addresses
  useEffect(() => {
    const loadGuestCart = async () => {
      const localCart = JSON.parse(localStorage.getItem("cart")) || [];
      if (!localCart.length) {
        setGuestCartItems([]);
        return;
      }
      try {
        const variantIds = localCart.map((i) => i.product_variant_id);
        const res = await axiosInstance.post("product-variants/bulk/", { variant_ids: variantIds });
        const enriched = res.data.map((v) => {
          const localItem = localCart.find((i) => i.product_variant_id === v.id);
          return { ...v, quantity: localItem?.quantity || 1 };
        });
        setGuestCartItems(enriched);
      } catch (err) {
        console.error(err);
        toast.error(err?.response?.data?.detail || "Failed to load cart items");
      }
    };

    const loadSavedAddresses = async () => {
      try {
        const res = await axiosInstance.get("shipping-addresses/");
        setShippingAddresses(res.data.results || []);
        if (res.data.results?.length) setSelectedAddressId(res.data.results[0].id);
      } catch (err) {
        console.error(err);
      }
    };

    if (!isAuthenticated && !buyNowItems.length) {
      navigate("/login", { state: { from: location.pathname } });
      loadGuestCart().finally(() => setLoading(false));
    } else {
      setLoading(true);
      refetchCart().finally(() => setLoading(false));
      loadSavedAddresses();
    }
  }, [isAuthenticated, navigate, location.pathname, refetchCart, buyNowItems.length]);

  const cartItems = getCartItems();

  const totalAmount = cartItems.reduce((acc, item) => {
    const variant = isAuthenticated ? item.product_variant_detail || {} : item || {};
    return acc + (variant?.price || item?.price || 0) * (item?.quantity || 1);
  }, 0);

  // Handle Place Order
 const handlePlaceOrder = async () => {
  // Get selected address (either existing or new)
  const selectedAddressPayload = selectedAddressId
    ? shippingAddresses.find(addr => addr.id === selectedAddressId)
    : newAddress;

  if (!selectedAddressPayload) {
    toast.error("Please select or add a shipping address");
    return;
  }

  if (!paymentMethod) {
    toast.error("Please select a payment method");
    return;
  }

  if (!cartItems.length) {
    toast.error("Your cart is empty");
    return;
  }

  const itemsPayload = buildItemsPayload(cartItems);

  try {
    if (paymentMethod === "Razorpay") {
      const orderId = await handleRazorpayPayment({
        order_id: pendingOrderId,
        items: itemsPayload,
        shipping_address: selectedAddressPayload, // send full object
      });
      setPendingOrderId(orderId);

      if (!buyNowItems.length && !isAuthenticated) localStorage.removeItem("cart");
      navigate(`/orders/${orderId}/`);
    } else {
      const res = await axiosInstance.post("checkout/cart/", {
        items: itemsPayload,
        shipping_address: selectedAddressPayload, // send full object
        payment_method: paymentMethod, // e.g., "Cash on Delivery"
      });

      if (!buyNowItems.length && !isAuthenticated) localStorage.removeItem("cart");
      toast.success("Order placed successfully");
      navigate(`/orders/${res.data.id}`);
    }
  } catch (error) {
    console.error(error);
    toast.error(error.response?.data?.detail || "Failed to place order");
  }
};


  if (loading || authLoading) return <p className="p-6">Loading cart...</p>;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Checkout</h1>
      {cartItems.length === 0 ? (
        <p>Your cart is empty</p>
      ) : (
        <>
          <CartItemList cartItems={cartItems} isAuthenticated={isAuthenticated} />
          <ShippingAddressSelector
            shippingAddresses={shippingAddresses}
            selectedAddressId={selectedAddressId}
            setSelectedAddressId={setSelectedAddressId}
            newAddress={newAddress}
            setNewAddress={setNewAddress}
          />
          <PaymentMethodSelector paymentMethod={paymentMethod} setPaymentMethod={setPaymentMethod} />
          <CheckoutSummary totalAmount={totalAmount} onPlaceOrder={handlePlaceOrder} />
        </>
      )}
    </div>
  );
};

export default Checkout;
