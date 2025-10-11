import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axiosInstance from "../../../api/axiosinstance";

const DeliverymanReturnDetail = ({ returnId, onClose, onUpdated }) => {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pickupStatus, setPickupStatus] = useState("pending");
  const [pickupComment, setPickupComment] = useState("");
  const [saving, setSaving] = useState(false);

  const fetchDetail = async () => {
    setLoading(true);
    try {
      const res = await axiosInstance.get(`returns/${returnId}`);
      setDetail(res.data);
      setPickupStatus(res.data.pickup_status_display.toLowerCase());
      setPickupComment(res.data.pickup_comment || "");
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!pickupStatus) return alert("Please select pickup status");
    setSaving(true);
    try {
      await axiosInstance.patch(`returns/${returnId}/update/`, {
        pickup_status: pickupStatus,
        pickup_comment: pickupComment,
      });
      onUpdated?.();
      onClose?.();
    } catch (error) {
      console.error(error);
      alert("Failed to update return request");
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [returnId]);

  return (
    <AnimatePresence>
  {returnId && (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm bg-black/40 p-4"
    >
      <motion.div
        initial={{ y: -40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 40, opacity: 0 }}
        className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl p-6 border border-gray-100"
      >
        {loading || !detail ? (
          <p className="text-center py-10 text-gray-400">Loading...</p>
        ) : (
          <>
            {/* Header */}
            <div className="flex justify-between items-center mb-6 border-b pb-3">
              <h2 className="text-2xl font-semibold text-gray-800">
                Return Request <span className="text-yellow-500">#{detail.id}</span>
              </h2>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-700 text-2xl font-bold transition"
              >
                ✕
              </button>
            </div>

            {/* Order Info */}
            <div className="mb-5 p-4 bg-gray-50 rounded-lg shadow-sm">
              <p className="text-gray-700">
                <span className="font-semibold">Order:</span> {detail.order.order_number}
              </p>
              <p className="text-gray-700 mt-1">
                <span className="font-semibold">Status:</span>{" "}
                <span className={`font-medium ${detail.order.status === "delivered" ? "text-green-600" : "text-yellow-500"}`}>
                  {detail.order.status.toUpperCase()}
                </span>
              </p>
              <p className="text-gray-700 mt-1">
                <span className="font-semibold">Total:</span> ₹{detail.order.total}
              </p>
            </div>

            {/* Product Info */}
            <div className="mb-5 flex gap-4 items-center p-4 bg-white border rounded-xl shadow-sm hover:shadow-md transition">
              <img
                src={detail.product_image}
                alt={detail.variant}
                className="w-28 h-28 object-cover rounded-xl border border-gray-100 shadow-sm"
              />
              <div className="flex-1">
                <p className="font-semibold text-lg text-gray-800">{detail.product}</p>
                <p className="text-gray-500 text-sm mt-1">{detail.variant}</p>
                <p className="text-gray-500 text-sm mt-1">Qty: {detail.order_item?.quantity}</p>
                <p className="text-gray-500 text-sm mt-1">Reason: {detail.reason}</p>
              </div>
            </div>

            {/* Shipping Info */}
            <div className="mb-5 p-4 bg-gray-50 rounded-lg shadow-sm">
              <p className="font-semibold text-gray-700 mb-2">Shipping Address</p>
              <p className="text-gray-600">{detail.shipping_address.full_name}</p>
              <p className="text-gray-600">{detail.shipping_address.phone_number}</p>
              <p className="text-gray-600">
                {detail.shipping_address.address}, {detail.shipping_address.locality}, {detail.shipping_address.city},{" "}
                {detail.shipping_address.state}, {detail.shipping_address.postal_code}
              </p>
            </div>

            {/* Pickup Status */}
            <div className="mb-6">
              <label className="block font-semibold mb-2 text-gray-700">Pickup Status</label>
              <select
                className="border rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-yellow-400 focus:border-yellow-400 transition"
                value={pickupStatus}
                onChange={(e) => setPickupStatus(e.target.value)}
              >
                <option value="pending">Pending</option>
                <option value="collected">Collected</option>
                <option value="rejected_pickup">Rejected at Pickup</option>
                <option value="damaged">Rejected - Damaged</option>
              </select>

              <label className="block font-semibold mt-4 mb-2 text-gray-700">Pickup Comment</label>
              <textarea
                className="border rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-yellow-400 focus:border-yellow-400 transition"
                rows={3}
                value={pickupComment}
                onChange={(e) => setPickupComment(e.target.value)}
                placeholder="Add any comments..."
              />
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3">
              <button
                onClick={onClose}
                className="px-5 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium transition"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-5 py-2 rounded-lg bg-yellow-500 hover:bg-yellow-600 text-white font-medium transition disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save"}
              </button>
            </div>
          </>
        )}
      </motion.div>
    </motion.div>
  )}
</AnimatePresence>

  );
};

export default DeliverymanReturnDetail;
