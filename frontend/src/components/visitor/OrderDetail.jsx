import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import axiosInstance from "../../api/axiosinstance";
import { handleRazorpayPayment } from "../../utils/payment";
import { useAuth } from "../../contexts/authContext";
import CancelReasonModal from "../helpers/CancelReasonModal";
import OrderDetailShimmer from "../../shimmer/OrderDetailShimmer";
import OrderTracker from "./OrderTracker";


const OrderDetail = () => {
  const { id: orderId } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [refund, setRefund] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCancelModal, setShowCancelModal] = useState(false);

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
               
        // Fetch refund status
        try {
          const refundRes = await axiosInstance.get(`orders/${orderId}/refund-status/`);
          if (refundRes.data?.refund_id) {
            setRefund(refundRes.data);
          }
        } catch (err) {
          console.warn("No refund info:", err.response?.data?.message || "No refund initiated");
        }

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

  if (loading || authLoading) return <OrderDetailShimmer/>;
  if (!order) return <p className="p-6">Order not found.</p>;

  const totalAmount = (order.items || []).reduce(
    (acc, item) => acc + (item.price || 0) * (item.quantity || 1),
    0
  );

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white shadow-md rounded-lg">
      <h1 className="text-3xl font-bold mb-6 border-b pb-3">Order #{order.id}</h1>

      {/* Shipping Address */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
        <h2 className="text-xl font-semibold mb-3">Shipping Address</h2>
        <p className="text-gray-700 font-medium">{order.shipping_address.full_name}</p>
        <p className="text-gray-700">
          {order.shipping_address.address}, {order.shipping_address.locality}, {order.shipping_address.region}
        </p>
        <p className="text-gray-700">
          {order.shipping_address.district}, {order.shipping_address.state}, {order.shipping_address.city}
        </p>
        <p className="text-gray-700">
          {order.shipping_address.postal_code}, {order.shipping_address.country}
        </p>
        <p className="text-gray-700">Phone: {order.shipping_address.phone_number}</p>
      </div>

      {/* Items */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-3">Order Items</h2>
        <ul className="divide-y border rounded-lg overflow-hidden">
          {order.items.map((item, idx) => {
              const variant = item.product_variant;
              const quantity = item.quantity || 1;
              const price = parseFloat(item.price || variant.price || 0);

              const imageUrl =
                variant.images?.[0]?.url ||
                variant.product_images?.[0] ||
                "/placeholder.png";
                         
              return (
                <li
                  key={variant.id || `${item.id}-${idx}`}
                  className="flex justify-between items-center p-4 hover:bg-gray-50 transition"
                >
                  <div className="flex items-center space-x-4">
                    <img
                      src={imageUrl}
                      alt={variant.product_name}
                      className="w-20 h-20 object-cover rounded-md shadow-sm"
                    />
                    <div>
                      <p className="font-semibold text-gray-800">
                        {variant.product_name}
                        {variant.variant_name && ` - ${variant.variant_name}`}
                      </p>
                      <p className="text-gray-500 text-sm">Qty: {quantity}</p>
                    </div>
                  </div>
                  <p className="text-gray-800 font-medium">
                    ₹{(price * quantity).toFixed(2)}
                  </p>
                </li>
              );
            })}

        </ul>
      </div>

      {/* Summary */}
      {/* Summary */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
        <h2 className="text-xl font-semibold mb-3">Order Summary</h2>

        <div className="flex justify-between mb-2">
          <span className="text-gray-700">Subtotal:</span>
          <span className="font-medium text-gray-900">
            ₹{parseFloat(order.subtotal || 0).toFixed(2)}
          </span>
        </div>

        <div className="flex justify-between mb-2">
          <span className="text-gray-700">Delivery Charge:</span>
          <span className="font-medium text-gray-900">
            ₹{parseFloat(order.delivery_charge || 0).toFixed(2)}
          </span>
        </div>

        <div className="flex justify-between mb-2 border-t pt-2">
          <span className="text-gray-700">Total:</span>
          <span className="font-bold text-gray-900">
            ₹{parseFloat(order.total || 0).toFixed(2)}
          </span>
        </div>

        <div className="flex justify-between mb-2">
          <span className="text-gray-700">Payment Method:</span>
          <span className="font-medium text-gray-900">
            {order.payment_method || "Not selected"}
          </span>
        </div>

        <div className="flex justify-between mb-2">
          <span className="text-gray-700">Payment Status:</span>
          <span
            className={
              order.is_paid
                ? "text-green-600 font-medium"
                : "text-red-600 font-medium"
            }
          >
            {order.is_paid ? "Paid" : "Pending"}
          </span>
        </div>

        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-3">Order Status</h2>
          <OrderTracker
              status={order.status}
              timestamps={{
                pending: order.created_at,
                processing: order.paid_at,
                shipped: order.shipped_at,
                delivered: order.delivered_at,
                cancelled: order.cancelled_at,
                refunded: order.refunded_at,
              }}
            />

        </div>

      


        {/* Refund Info */}
        {refund && (
          <div className="mt-4 border-t pt-4">
            <h3 className="text-lg font-semibold mb-2">Refund Details</h3>
            <div className="flex justify-between mb-1">
              <span className="text-gray-700">Refund ID:</span>
              <span className="text-gray-900 font-medium">{refund.refund_id}</span>
            </div>
            <div className="flex justify-between mb-1">
              <span className="text-gray-700">Status:</span>
              <span
                className={
                  refund.refund_status === "completed"
                    ? "text-green-600 font-medium"
                    : refund.refund_status === "pending"
                    ? "text-yellow-600 font-medium"
                    : "text-red-600 font-medium"
                }
              >
                {refund.refund_status}
              </span>
            </div>
            {refund.refund_status === "pending" && (
              <div className="mt-2 text-sm text-yellow-700 bg-yellow-100 px-3 py-2 rounded">
                Refund is pending. Please allow 3–5 business days for processing.
              </div>
            )}
            {refund.refunded_at && (
              <div className="flex justify-between mb-1">
                <span className="text-gray-700">Refunded At:</span>
                <span className="text-gray-900 font-medium">{new Date(refund.refunded_at).toLocaleString()}</span>
              </div>
            )}
            {refund.refund_reason && (
              <div className="flex justify-between">
                <span className="text-gray-700">Reason:</span>
                <span className="text-gray-900 font-medium">{refund.refund_reason}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Order Actions */}
{(!order.is_paid || (order.cancelable && order.status !== "cancelled")) && (
  <div className="flex flex-col sm:flex-row justify-end gap-3 mt-4">
    {/* Pay Now */}
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
        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition w-full sm:w-auto"
      >
        Pay Now
      </button>
    )}

    {/* Cancel Order */}
    {order.cancelable && order.status !== "cancelled" && (
      <button
        onClick={() => setShowCancelModal(true)}   // ✅ wrap in arrow function
        className="px-6 py-2 bg-red-600 text-white rounded-lg 
        hover:bg-red-700 transition w-full sm:w-auto"
      >
        Cancel Order
      </button>
    )}

    <CancelReasonModal
    isOpen={showCancelModal}
      onClose={() => setShowCancelModal(false)}
      onConfirm={async (reason) => {
        try {
          const res = await axiosInstance.post(`orders/${orderId}/cancel/`, {
            cancel_reason: reason,
          });
          setOrder(res.data.order);
          navigate("/orders");
          toast.success(res.data.message || "Order cancelled successfully");
        } catch (err) {
          console.error("Cancel failed:", err);
          toast.error(err.response?.data?.message || "Failed to cancel order");
        } finally {
          setShowCancelModal(false);
        }
      }}
    />
  </div>
)}

    </div>
  );
};

export default OrderDetail;