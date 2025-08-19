import axiosInstance from "../api/axiosinstance";
import { toast } from "react-toastify";

// Load Razorpay SDK dynamically
const loadRazorpayScript = () =>
  new Promise((resolve, reject) => {
    if (window.Razorpay) return resolve(true);

    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve(true);
    script.onerror = () => reject(new Error("Razorpay SDK failed to load"));
    document.body.appendChild(script);
  });

export const handleRazorpayPayment = async ({
  orderId,
  items,
  shipping_address,
  payment_method = "Razorpay",
  isBuyNowFlow = false,
  onSuccess,
}) => {
  try {
    await loadRazorpayScript();

    if (!orderId) {
      if (!items || !shipping_address) {
        throw new Error("Items and shipping address are required for new orders");
      }

      const endpoint = isBuyNowFlow ? "checkout/buy-now/" : "checkout/cart/";
      const orderRes = await axiosInstance.post(endpoint, {
        items,
        shipping_address,
        payment_method,
      });

      orderId = orderRes.data.order?.id || orderRes.data.id;
    }

    const razorpayRes = await axiosInstance.post(`orders/${orderId}/razorpay/`);
    const { razorpay_order_id, amount, currency, razorpay_key } = razorpayRes.data;

    if (!razorpay_order_id) throw new Error("Failed to get Razorpay order ID from backend");

    return new Promise((resolve, reject) => {
      const options = {
        key: razorpay_key,
        amount,
        currency,
        name: "My Shop",
        order_id: razorpay_order_id,
        handler: async (response) => {
          try {
            const payload = {
              razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              order_id: orderId,
            };

            await axiosInstance.post("orders/razorpay/verify/", payload);
            toast.success("Payment successful!");
            if (onSuccess) onSuccess(orderId);
            resolve(orderId);
          } catch (err) {
            console.error(err);
            toast.error(err.response?.data?.detail || "Payment verification failed");
            reject(err);
          }
        },
        modal: {
          ondismiss: () => {
            toast.info("Payment was cancelled");
            reject(new Error("Payment cancelled"));
          },
        },
        theme: { color: "#3399cc" },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    });
  } catch (err) {
    console.error(err);
    toast.error(err.message || "Failed to initiate Razorpay payment");
    throw err;
  }
};