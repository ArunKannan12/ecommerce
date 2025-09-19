import React, { useEffect, useState } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import axiosInstance from "../../../api/axiosinstance";
import { toast } from "react-toastify";

const ReturnRequest = () => {
  const { orderId, returnId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [order, setOrder] = useState(null);
  const [request, setRequest] = useState(null);
  const [reason, setReason] = useState("");
  const [upi, setUpi] = useState("");
  const [loading, setLoading] = useState(true);

  const itemId = searchParams.get("item");

  useEffect(() => {
  
    const fetchData = async () => {
      setLoading(true);
      try {
        if (returnId) {
          // Viewing an existing return request
          const res = await axiosInstance.get(`/returns/${returnId}/`);
          setRequest(res.data);
          console.log(request,'req');
          
          setOrder(res.data.order); // API returns the order inside the request 
        } else if (orderId) {
          // Fetch the order for creating a new return
          const orderRes = await axiosInstance.get(`/orders/${orderId}/`);
          setOrder(orderRes.data);
        } else {
          toast.error("No order specified");
          navigate("/orders");
        }
      } catch (err) {
        console.error(err);
        toast.error("Failed to fetch order or return request");
        navigate("/orders");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [orderId, returnId, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!reason) return toast.error("Please provide a reason");
    if (order.payment_method.toLowerCase() === "cod" && !upi) {
      return toast.error("Please provide your UPI ID for COD payment");
    }

    const payload = {
      order_id: orderId,
      order_item_id: itemId || order.items[0]?.id,
      reason,
    };

    if (order.payment_method.toLowerCase() === "cod") payload.user_upi = upi;

    try {
      setLoading(true);
      const res = await axiosInstance.post(`/returns/create/`, payload);
      setRequest(res.data);
      toast.success("Return request submitted successfully");
      navigate(`/returns/${res.data.id}`);
    } catch (err) {
      toast.error(err.response?.data?.message || "Failed to submit return request");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <p className="text-center py-10 text-gray-500">Loading...</p>;
  if (!order) return <p className="text-center py-10 text-gray-500">Order not found.</p>;

  return (
    <div className="max-w-4xl mx-auto mt-8 px-4 sm:px-6 py-6 bg-white rounded-3xl shadow-2xl font-sans">
  <h1 className="text-2xl sm:text-4xl font-extrabold text-gray-900 mb-8 text-center tracking-tight">
    {request ? "Return Request Summary" : "Initiate a Return"}
  </h1>

  {request ? (
    <div className="space-y-6 sm:space-y-8">
      {/* Product Overview */}
      <div className="flex flex-wrap sm:flex-nowrap items-center gap-4 sm:gap-6 bg-gray-50 p-4 sm:p-6 rounded-2xl shadow-md">
        <img
          src={request.product_image || request.variant_images?.[0]}
          alt={request.variant}
          className="w-24 h-24 sm:w-28 sm:h-28 object-cover rounded-xl border"
        />
        <div className="flex-1 space-y-1">
          <h2 className="text-lg sm:text-xl font-semibold text-gray-800">
            {request.product} {request.variant && `- ${request.variant}`}
          </h2>
          <p className="text-gray-600 text-sm">Qty: {request.order_item.quantity}</p>
          <p className="text-gray-600 text-sm">Price Paid: ₹{request.order_item.price}</p>
        </div>
      </div>

      {/* Return Details */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6 text-sm">
        <div>
          <p><strong>Reason:</strong> {request.reason}</p>
          <p>
            <strong>Status:</strong>{" "}
            <span className={`inline-block px-2 py-1 rounded-full text-white text-xs font-semibold ${
              request.status === "pending" ? "bg-yellow-500" :
              request.status === "approved" ? "bg-green-600" :
              "bg-gray-500"
            }`}>
              {request.status.toUpperCase()}
            </span>
          </p>
          {request.return_days_remaining != null && (
            <p><strong>Return Window:</strong> {request.return_days_remaining} days left</p>
          )}
        </div>
        <div>
          <p><strong>Refund Amount:</strong> ₹{request.refund_amount}</p>
          <p><strong>Refund Method:</strong> {request.refund_method_display}</p>
        </div>
      </div>

      {/* Flipkart-style Progress Tracker */}
      {/* Flipkart-style Progress Tracker */}
<div className="mt-10">
  <h3 className="text-xl font-bold text-gray-900 mb-6 text-center">📦 Return Progress</h3>
  <div className="flex justify-center">
    <div className="w-full max-w-md">
      <div className="relative border-l-2 border-gray-300 pl-6 space-y-8">

        {[  
          {
            label: "Request Submitted",
            status: "completed",
            timestamp: new Date(request.created_at).toLocaleString(),
            color: "green"
          },
          {
            label: "Pickup",
            status: request.pickup_status_display.toLowerCase(),
            note: request.pickup_comment,
            color: request.pickup_status_display.toLowerCase() === "completed" ? "green" : "yellow"
          },
          {
            label: "Warehouse",
            status: request.warehouse_status_display.toLowerCase(),
            note: request.warehouse_comment,
            color: request.warehouse_status_display.toLowerCase() === "verified" ? "green" : "yellow"
          },
          {
            label: "Admin",
            status: request.admin_status_display.toLowerCase(),
            note: request.admin_comment,
            color: request.admin_status_display.toLowerCase() === "approved" ? "green" : "yellow"
          },
          {
            label: "Refund",
            status: request.is_refunded ? "completed" : "pending",
            note: request.is_refunded ? `Refunded on ${request.refunded_at_human}` : null,
            color: request.is_refunded ? "green" : "gray",
            extra: [
              `Amount: ₹${request.refund_amount}`,
              `Method: ${request.refund_method_display}`
            ]
          }
        ].map((step, idx) => (
          <div key={idx} className="relative">
            <div className={`absolute -left-[14px] top-1 w-4 h-4 rounded-full border-2 border-white shadow-md ${
              step.color === "green" ? "bg-green-500" :
              step.color === "yellow" ? "bg-yellow-400" :
              "bg-gray-400"
            }`}></div>

            <p className="font-semibold text-gray-800">{step.label}</p>
            {step.status && (
              <p className="text-sm text-gray-600 capitalize">Status: {step.status}</p>
            )}
            {step.timestamp && (
              <p className="text-sm text-gray-500">Time: {step.timestamp}</p>
            )}
            {step.note && (
              <p className="text-sm text-gray-600 italic">Note: {step.note}</p>
            )}
            {step.extra?.map((line, i) => (
              <p key={i} className="text-sm text-gray-600">{line}</p>
            ))}
          </div>
        ))}
      </div>
    </div>
  </div>
</div>

      {/* Shipping Address */}
      <div className="bg-gray-50 p-4 sm:p-6 rounded-xl border text-sm">
        <h3 className="font-semibold text-base mb-2">Shipping Address</h3>
        <p>{request.shipping_address.full_name}</p>
        <p>{request.shipping_address.phone_number}</p>
        <p className="text-gray-600">
          {request.shipping_address.address}, {request.shipping_address.locality},{" "}
          {request.shipping_address.city}, {request.shipping_address.district},{" "}
          {request.shipping_address.state} - {request.shipping_address.postal_code},{" "}
          {request.shipping_address.country}
        </p>
      </div>

      {/* Order Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6 text-sm">
        <p><strong>Order Total:</strong> ₹{request.order.total}</p>
        <p><strong>Delivery Charge:</strong> ₹{request.delivery_charge}</p>
        <p><strong>Payment Method:</strong> {request.order.payment_method}</p>
        <p><strong>Paid:</strong> {request.order.is_paid ? "Yes" : "No"}</p>
        <p><strong>Order Date:</strong> {new Date(request.order.created_at).toLocaleString()}</p>
        {request.order.paid_at && (
          <p><strong>Paid At:</strong> {new Date(request.order.paid_at).toLocaleString()}</p>
        )}
      </div>

      <div className="text-center mt-6 sm:mt-8">
        <button
          onClick={() => navigate(-1)}
          className="w-full sm:w-auto px-6 py-3 bg-gray-900 text-white rounded-lg hover:bg-gray-700 transition"
        >
          Go Back
        </button>
      </div>
    </div>
  ) : (
    <form onSubmit={handleSubmit} className="space-y-6 text-sm">
      <div>
        <label className="block font-medium mb-2">Reason for Return</label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Describe your reason clearly"
          rows={5}
          className="w-full border border-gray-300 rounded-xl p-4 focus:outline-none focus:ring-2 focus:ring-yellow-400 shadow-sm"
        />
      </div>

      {order.payment_method.toLowerCase() === "cod" && (
        <div>
          <label className="block font-medium mb-2">UPI ID (required)</label>
          <input
            type="text"
            value={upi}
            onChange={(e) => setUpi(e.target.value)}
            placeholder="Enter your UPI ID"
                        className="w-full border border-gray-300 rounded-xl p-4 focus:outline-none focus:ring-2 focus:ring-yellow-400 shadow-sm"
          />
          <p className="text-xs text-gray-500 mt-1">Required for COD refunds</p>
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full px-6 py-3 bg-yellow-500 text-white rounded-xl hover:bg-yellow-600 transition font-semibold shadow-md disabled:opacity-50"
      >
        {loading ? "Submitting..." : "Submit Return Request"}
      </button>
    </form>
  )}
</div>

  );
};

export default ReturnRequest;
