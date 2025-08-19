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

const BUY_NOW_KEY = "buyNowMinimal";

const Checkout = () => {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [buyNowItems, setBuyNowItems] = useState([]);
  const [guestCartItems, setGuestCartItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [paymentMethod, setPaymentMethod] = useState("");
  const [pendingOrderId, setPendingOrderId] = useState(null);
  const [selectedAddress, setSelectedAddress] = useState(null);

  const { data: authCartData, refetch: refetchAuthCart } = useGetCartQuery(undefined, {
    skip: !isAuthenticated,
  });

  useEffect(() => {
    const enrichBuyNowItems = async () => {
      const stored = sessionStorage.getItem(BUY_NOW_KEY);
      if (!stored) return;

      try {
        const minimalItems = JSON.parse(stored);
        const variantIds = minimalItems.map((i) => i.product_variant_id);
        const res = await axiosInstance.post("product-variants/bulk/", { variant_ids: variantIds });

        const enriched = res.data.map((variant) => {
          const localItem = minimalItems.find((i) => i.product_variant_id === variant.id);
          return {
            id: variant.id,
            product_variant_id: variant.id,
            quantity: localItem?.quantity || 1,
            price: Number(variant.price || 0),
            productName: variant.product_name || "Product",
            variantName: variant.variant_name || "Default",
            imageUrl: variant.product_images?.[0] || "/placeholder.png",
          };
        });

        setBuyNowItems(enriched);
      } catch (err) {
        toast.error("Failed to load Buy Now items");
      }
    };

    enrichBuyNowItems();
  }, []);

  useEffect(() => {
    const loadGuestCart = async () => {
      if (!isAuthenticated && !buyNowItems.length) {
        const localCart = JSON.parse(localStorage.getItem("cart") || "[]");
        if (!localCart.length) {
          setGuestCartItems([]);
          return;
        }

        try {
          const variantIds = localCart.map((i) => i.product_variant_id);
          const res = await axiosInstance.post("product-variants/bulk/", { variant_ids: variantIds });

          const enriched = res.data.map((variant) => {
            const localItem = localCart.find((i) => i.product_variant_id === variant.id);
            const basePrice = Number(variant.product_base_price ?? variant.price ?? 0);
            const extraPrice = Number(variant.additional_price ?? 0);

            return {
              id: variant.id,
              product_variant_id: variant.id,
              quantity: localItem?.quantity || 1,
              price: basePrice + extraPrice,
              productName: variant.product_name || "Product",
              variantName: variant.variant_name || "",
              imageUrl: variant.product_images?.[0] || "/placeholder.png",
            };
          });

          setGuestCartItems(enriched);
        } catch (err) {
          toast.error(err?.response?.data?.detail || "Failed to load cart items");
        }
      }
    };

    setLoading(true);
    if (isAuthenticated) refetchAuthCart().finally(() => setLoading(false));
    loadGuestCart().finally(() => setLoading(false));
  }, [isAuthenticated, refetchAuthCart, buyNowItems.length]);

  const getVariantImage = (item) => {
    if (item.variant?.images?.length) return item.variant.images[0].url || "/placeholder.png";
    if (item.product?.images?.length) return item.product.images[0].url || "/placeholder.png";
    return item.imageUrl || "/placeholder.png";
  };

  const cartItems = buyNowItems.length
    ? buyNowItems.map((item) => ({ ...item, imageUrl: getVariantImage(item) }))
    : isAuthenticated && authCartData?.length
    ? authCartData.map((item) => ({
        id: item.product_variant_detail?.id || item.id,
        productName: item.product_variant_detail?.product_name || "Product",
        variantName: item.product_variant_detail?.variant_name || "",
        quantity: item.quantity || 1,
        price:
          item.price ??
          (Number(item.product_variant_detail?.product_base_price ?? 0) +
            Number(item.product_variant_detail?.additional_price ?? 0)),
        imageUrl: getVariantImage({
          variant: item.product_variant_detail,
          product: item.product,
          imageUrl: item.imageUrl,
        }),
        product_variant_id: item.product_variant_detail?.id,
      }))
    : guestCartItems.map((item) => ({ ...item, imageUrl: getVariantImage(item) }));

  const totalAmount = cartItems.reduce((acc, item) => acc + item.price * item.quantity, 0);

  const buildItemsPayload = (items) =>
    items.map((item) => ({
      product_variant_id: item.product_variant_id,
      quantity: item.quantity,
    }));

  const handlePlaceOrder = async () => {
    const isBuyNowFlow = buyNowItems?.length > 0;
    const itemsToUse = isBuyNowFlow ? buyNowItems : cartItems;

    if (!itemsToUse.length) {
      toast.error("Your cart is empty");
      return;
    }

    if (!selectedAddress) {
      toast.error("Please select a shipping address");
      return;
    }

    if (!paymentMethod) {
      toast.error("Please select a payment method");
      return;
    }

    const { full_name, phone_number, address, city, postal_code, country } = selectedAddress;
    const cleanAddress = { full_name, phone_number, address, city, postal_code, country };
    const itemsPayload = buildItemsPayload(itemsToUse);

    try {
      let orderId;

      if (paymentMethod === "Razorpay") {
        orderId = await handleRazorpayPayment({
          order_id: pendingOrderId,
          items: itemsPayload,
          shipping_address: selectedAddress.id,
          isBuyNowFlow,
        });
        setPendingOrderId(orderId);
      } else {
        const endpoint = isBuyNowFlow ? "checkout/buy-now/" : "checkout/cart/";
        const payload = {
          items: itemsPayload,
          shipping_address: selectedAddress.id,
          payment_method: paymentMethod,
        };
        console.log("Checkout payload:", payload);
        const res = await axiosInstance.post(endpoint, payload);
        orderId = res.data.id;
      }

      toast.success("Order placed successfully");
      if (!isBuyNowFlow && !isAuthenticated) localStorage.removeItem("cart");
      if (isBuyNowFlow) sessionStorage.removeItem(BUY_NOW_KEY);
      setPendingOrderId(null);
      setBuyNowItems([]);
      navigate(`/orders/${orderId}/`);
    } catch (error) {
      console.error("[Checkout] Order placement failed", error.response?.data || error.message);
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
          <CartItemList cartItems={cartItems} />
          <ShippingAddressSelector
            selectedAddress={selectedAddress}
            setSelectedAddress={setSelectedAddress}
          />
          <PaymentMethodSelector paymentMethod={paymentMethod} setPaymentMethod={setPaymentMethod} />
          <CheckoutSummary totalAmount={totalAmount} onPlaceOrder={handlePlaceOrder} />
        </>
      )}
    </div>
  );
};

export default Checkout;