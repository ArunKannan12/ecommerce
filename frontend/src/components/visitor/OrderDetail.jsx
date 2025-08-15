import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import axiosInstance from "../../api/axiosinstance";
import { useAuth } from "../../contexts/AuthContext";
import { handleRazorpayPayment } from "../../utils/payment";

const OrderDetail = () => {
  const { id: orderId } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  const { isAuthenticated, loading: authLoading } = useAuth();

  useEffect(() => {
    if (authLoading) return;

    if (!isAuthenticated) {
      navigate("/login", { state: { from: `/orders/${orderId}` } });
      return;
    }

    const fetchOrder = async () => {
      setLoading(true);
      try {
        const res = await axiosInstance.get(`orders/${orderId}/`);
        setOrder(res.data);
      } catch (error) {
        console.error("Failed to fetch order:", error);
        toast.error(error.response?.data?.detail || "Failed to fetch order details");
        navigate("/orders");
      } finally {
        setLoading(false);
      }
    };

    fetchOrder();
  }, [orderId, isAuthenticated, authLoading, navigate]);

  if (loading || authLoading) return <p className="p-6">Loading order...</p>;
  if (!order) return <p className="p-6">Order not found.</p>;

  const totalAmount = (order.items || []).reduce(
    (acc, item) => acc + (item.price || 0) * (item.quantity || 1),
    0
  );

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Order #{order.id}</h1>

      {/* Shipping Address */}
      <div className="mb-6">
        <h2 className="font-semibold mb-2">Shipping Address</h2>
        <p>{order.shipping_address.full_name}</p>
        <p>{order.shipping_address.address}, {order.shipping_address.city}</p>
        <p>{order.shipping_address.postal_code}, {order.shipping_address.country}</p>
        <p>Phone: {order.shipping_address.phone_number}</p>
      </div>

      {/* Items */}
      <div className="mb-6">
        <h2 className="font-semibold mb-2">Items</h2>
        <ul className="divide-y">
          {order.items.map((item, idx) => {
            const variant = item.product_variant;
            const quantity = item.quantity || 1;
            const price = parseFloat(item.price || variant.price || 0);
            const imageUrl = variant.product_images?.[0]
              ? `http://localhost:8000${variant.product_images[0]}`
              : "/placeholder.png";

            return (
              <li key={variant.id || `${item.id}-${idx}`} className="py-4 flex justify-between items-center">
                <div className="flex items-center space-x-4">
                  <img
                    src={imageUrl}
                    alt={variant.product_name}
                    className="w-20 h-20 object-cover rounded-md"
                  />
                  <div>
                    <p className="font-semibold">
                      {variant.product_name} - {variant.variant_name}
                    </p>
                    <p className="text-sm text-gray-500">Qty: {quantity}</p>
                  </div>
                </div>
                <p className="text-gray-800 font-medium">₹{(price * quantity).toFixed(2)}</p>
              </li>
            );
          })}
        </ul>
      </div>

      {/* Total, Payment Method & Status */}
      <div className="mb-6">
        <p className="text-xl font-bold">Total: ₹{totalAmount.toFixed(2)}</p>
        <p className="mt-2">
          Payment Status:{" "}
          <span className={order.is_paid ? "text-green-600" : "text-red-600"}>
            {order.is_paid ? "Paid" : "Pending"}
          </span>
        </p>
        <p className="mt-1">Order Status: {order.status || "Processing"}</p>
        <p className="mt-1">
          Payment Method:{" "}
          <span className="font-medium">{order.payment_method || "Not selected"}</span>
        </p>
      </div>

      {/* Pay Now Button */}
      {!order.is_paid && order.payment_method === "Razorpay" && (
        <button
          onClick={async () => {
            try {
              await handleRazorpayPayment({
                orderId,
                onSuccess: async () => {
                  const updated = await axiosInstance.get(`orders/${orderId}/`);
                  setOrder(updated.data);
                  toast.success("Payment successful");
                },
              });
            } catch (err) {
              console.error(err);
              toast.error(err.response?.data?.detail || "Failed to initiate payment");
            }
          }}
          className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Pay Now
        </button>
      )}
    </div>
  );
};

export default OrderDetail;
