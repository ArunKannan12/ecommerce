import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import axiosInstance from "../../api/axiosinstance";
import { useAuth } from "../../contexts/authContext";
import OrderDetailShimmer from "../../shimmer/OrderDetailShimmer";
import OrderTracker from "./OrderTracker";

const OrderDetail = () => {
  const { id: orderId } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [refund, setRefund] = useState(null);
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
        
        
        // Fetch refund status
        try {
          const refundRes = await axiosInstance.get(`orders/${orderId}/refund-status/`);
          if (refundRes.data?.refund_id) setRefund(refundRes.data);
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

  if (loading || authLoading) return <OrderDetailShimmer />;
  if (!order) return <p className="p-6">Order not found.</p>;

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white shadow-lg rounded-xl">
      <h1 className="text-3xl font-bold mb-6 border-b pb-3">Order #{order.id}</h1>

      {/* Shipping Address */}
      <div className="mb-6 p-5 bg-gray-50 rounded-xl border">
        <h2 className="text-xl font-semibold mb-3">Shipping Address</h2>
        <p className="text-gray-800 font-medium">{order.shipping_address.full_name}</p>
        <p className="text-gray-600">
          {order.shipping_address.address}, {order.shipping_address.locality}, {order.shipping_address.region}
        </p>
        <p className="text-gray-600">
          {order.shipping_address.district}, {order.shipping_address.state}, {order.shipping_address.city}
        </p>
        <p className="text-gray-600">
          {order.shipping_address.postal_code}, {order.shipping_address.country}
        </p>
        <p className="text-gray-600">Phone: {order.shipping_address.phone_number}</p>
      </div>

      {/* Order Items */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-3">Order Items</h2>
        <ul className="divide-y border rounded-xl overflow-hidden">
          {order.items.map((item) => {
            const variant = item.product_variant;
            const quantity = item.quantity || 1;
            const price = parseFloat(item.price || variant.final_price || 0);
            const imageUrl = variant.images?.[0]?.url || "/placeholder.png";

            return (
              <li key={item.id} className="flex justify-between items-center p-4 hover:bg-gray-50 transition rounded-xl">
                <div className="flex items-center space-x-4">
                  <img src={imageUrl} alt={variant.product_name} className="w-20 h-20 object-cover rounded-xl shadow-sm" />
                  <div>
                    <p className="font-semibold text-gray-800">
                      {variant.product_name}{variant.variant_name && ` - ${variant.variant_name}`}
                    </p>
                    <p className="text-gray-500 text-sm">Qty: {quantity}</p>

                    {/* Premium badges for return & replacement */}
                    <div className="flex gap-2 mt-1">
                      {variant.allow_return && item.return_remaining_days > 0 && (
                        <span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                          Return: {item.return_remaining_days} day{item.return_remaining_days !== 1 && "s"}
                        </span>
                      )}
                      {variant.allow_replacement && item.replacement_remaining_days > 0 && (
                        <span className="px-2 py-0.5 bg-indigo-100 text-indigo-800 text-xs rounded-full">
                          Replacement: {item.replacement_remaining_days} day{item.replacement_remaining_days !== 1 && "s"}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <p className="text-gray-800 font-medium">₹{(price * quantity).toFixed(2)}</p>
              </li>
            );
          })}
        </ul>
      </div>

      {/* Order Summary */}
      <div className="mb-6 p-5 bg-gray-50 rounded-xl border">
        <h2 className="text-xl font-semibold mb-3">Order Summary</h2>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-700">Subtotal:</span>
            <span className="font-medium text-gray-900">₹{parseFloat(order.subtotal || 0).toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-700">Delivery Charge:</span>
            <span className="font-medium text-gray-900">₹{parseFloat(order.delivery_charge || 0).toFixed(2)}</span>
          </div>
          <div className="flex justify-between border-t pt-2 font-bold">
            <span className="text-gray-700">Total:</span>
            <span className="text-gray-900">₹{parseFloat(order.total || 0).toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-700">Payment Method:</span>
            <span className="font-medium text-gray-900">{order.payment_method || "Not selected"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-700">Payment Status:</span>
            <span className={order.is_paid ? "text-green-600 font-medium" : "text-red-600 font-medium"}>
              {order.is_paid ? "Paid" : "Pending"}
            </span>
          </div>
        </div>

        <div className="mt-4">
          <h3 className="text-lg font-semibold mb-2">Order Status</h3>
          <OrderTracker
            status={order.status}
            paymentMethod={order.payment_method}
            timestamps={{
              pending: order.created_at,
              processing: order.paid_at,
              packed: order.items[0]?.packed_at,
              shipped: order.items[0]?.shipped_at,
              out_for_delivery: order.items[0]?.out_for_delivery_at,
              delivered: order.items[0]?.delivered_at,
              cancelled: order.cancelled_at,
              refunded: order.refunded_at,
            }}
            cancel_info={
              order.cancelled_at && {
                cancel_reason: order.cancel_reason,
                cancelled_at: order.cancelled_at,
                cancelled_by_role: order.cancelled_by?.role || "User",
              }
            }
            return_request={order.return_request?.[0]}
            replacement_request={order.replacement_request?.[0]}
          />
        </div>
      </div>

      {/* Returns & Replacements */}
     {order.status === "delivered" && (
      <div className="mt-6 p-5 bg-gray-50 rounded-xl">
        <h2 className="text-xl font-semibold mb-4">Returns & Replacements</h2>
        <div className="flex flex-wrap gap-3">
          {order.items.map((item) => {
            const returnEligible =
              item.product_variant.allow_return && item.return_remaining_days > 0;
            const replacementEligible =
              item.product_variant.allow_replacement && item.replacement_remaining_days > 0;

            if (!returnEligible && !replacementEligible) return null;

            // Check if any return or replacement request exists for this order
            const itemReturnRequest =
              order.return_request?.length > 0 ? order.return_request[0] : null;
            const itemReplacementRequest =
              order.replacement_request?.length > 0 ? order.replacement_request[0] : null;

            return (
              <React.Fragment key={item.id}>
                {/* Return request exists */}
                {itemReturnRequest ? (
                  <button
                    onClick={() => navigate(`/returns/${itemReturnRequest.id}`)}
                    className="px-4 py-1 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
                  >
                    View Return Request
                  </button>
                ) : 
                /* Replacement request exists */
                itemReplacementRequest ? (
                  <button
                    onClick={() => navigate(`/replacements/${itemReplacementRequest.id}`)}
                    className="px-4 py-1 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
                  >
                    View Replacement Request
                  </button>
                ) : (
                  /* If neither exists, show eligible buttons */
                  <>
                    {returnEligible && (
                      <button
                        onClick={() =>
                          navigate(`/returns/create/${order.id}?item=${item.id}`)
                        }
                        className="px-4 py-1 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition"
                      >
                        Request Return
                      </button>
                    )}
                    {replacementEligible && (
                      <button
                        onClick={() =>
                          navigate(`/replacements/create/${order.id}?item=${item.id}`)
                        }
                        className="px-4 py-1 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition"
                      >
                        Request Replacement
                      </button>
                    )}
                  </>
                )}
              </React.Fragment>
            );
          })}

          {/* Fallback if no items eligible */}
          {!order.items.some(
            (item) =>
              (item.product_variant.allow_return && item.return_remaining_days > 0) ||
              (item.product_variant.allow_replacement &&
                item.replacement_remaining_days > 0)
          ) && (
            <p className="text-gray-500 text-sm">
              No items eligible for return or replacement.
            </p>
          )}
        </div>
      </div>
)}


    </div>
  );
};

export default OrderDetail;
