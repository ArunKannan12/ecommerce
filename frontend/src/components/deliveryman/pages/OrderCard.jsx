import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import axiosInstance from "../../../api/axiosinstance";

const OrderCard = ({ order, refreshOrders }) => {
  const [loadingIds, setLoadingIds] = useState([]); // track loading buttons
  const [otpInputs, setOtpInputs] = useState({}); // OTP per item

  useEffect(() => {
    const newState = { ...otpInputs };
    order.items.forEach((item) => {
      if (!newState[item.id]) {
        newState[item.id] = {
          value: "",
          sent: item.pending_otp ? false : true,
          verified: item.otp_verified || false,
        };
      }
    });
    setOtpInputs(newState);
  }, [order.items]);

  const isItemDone = (item) => ["delivered", "failed"].includes(item.status);

  const handleAction = async (action, itemId = null) => {
    const targetId = itemId || order.id;
    setLoadingIds((prev) => [...prev, targetId]);

    try {
      const payload = { action };
      if (itemId) payload.order_item_id = itemId;
      if (action === "verify_otp") payload.otp = otpInputs[itemId].value;
      if (["mark_failed", "reschedule"].includes(action))
        payload.order_number = order.order_number;

      await axiosInstance.post("deliveryman/orders/action/", payload);

      setOtpInputs((prev) => {
        const newState = { ...prev };
        if (action === "send_otp" || action === "resend_otp") {
          newState[itemId] = { ...newState[itemId], sent: true, value: "" };
        }
        if (action === "verify_otp") {
          newState[itemId] = { ...newState[itemId], verified: true, sent: false, value: "" };
        }
        return newState;
      });

      refreshOrders?.();
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.error || "Something went wrong");
    } finally {
      setLoadingIds((prev) => prev.filter((id) => id !== targetId));
    }
  };

  return (
    <motion.div
      key={order.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className="bg-white p-4 md:p-6 rounded-2xl shadow-lg flex flex-col justify-between hover:shadow-2xl transition-shadow"
    >
      {/* Order Info */}
      <div className="mb-4 border-b pb-3">
        <h2 className="text-xl md:text-2xl font-bold">{order.order_number}</h2>
        <p className="text-gray-500 text-sm mt-1">Customer: {order.customer_name}</p>
        <p className="text-gray-400 text-sm mt-0.5">Status: {order.status}</p>
      </div>

      {/* Shipping Address */}
      <div className="mb-4 p-3 border rounded-lg bg-gray-50">
        <h3 className="font-semibold mb-1">Shipping Address</h3>
        <p>{order.shipping_address.full_name}</p>
        <p>{order.shipping_address.address}</p>
        <p className="text-sm">
          {order.shipping_address.locality}, {order.shipping_address.city}, {order.shipping_address.state} - {order.shipping_address.postal_code}
        </p>
        <p className="text-sm">Phone: {order.shipping_address.phone_number}</p>
      </div>

      {/* Items */}
      <div className="mb-4">
        <h3 className="font-semibold mb-2">Items</h3>
        <div className="space-y-3">
          {order.items.map((item) => {
            const otp = otpInputs[item.id] || { value: "", sent: false, verified: false };
            const done = isItemDone(item);

            return (
              <div
                key={item.id}
                className="flex flex-col sm:flex-row justify-between items-start sm:items-center p-3 border rounded-lg bg-gray-50"
              >
                <span className="font-medium">{item.product_name}</span>

                {/* OTP Actions */}
                {!otp.sent && !otp.verified && !done && (
                  <button
                    className="mt-2 px-4 py-2 bg-yellow-500 text-white rounded-lg"
                    disabled={loadingIds.includes(item.id)}
                    onClick={() => handleAction("send_otp", item.id)}
                  >
                    {loadingIds.includes(item.id) ? "Sending..." : "Send OTP"}
                  </button>
                )}

                {otp.sent && !otp.verified && !done && (
                  <div className="flex flex-col sm:flex-row sm:items-center gap-2 mt-2 w-full sm:w-auto">
                    <input
                      type="text"
                      placeholder="Enter OTP"
                      value={otp.value}
                      onChange={(e) =>
                        setOtpInputs((prev) => ({ ...prev, [item.id]: { ...prev[item.id], value: e.target.value } }))
                      }
                      className="border px-2 py-1 rounded-md w-full sm:w-24"
                    />
                    <div className="flex gap-2 mt-2 sm:mt-0">
                      <button
                        className="px-3 py-1 bg-green-500 text-white rounded-md"
                        disabled={loadingIds.includes(item.id)}
                        onClick={() => handleAction("verify_otp", item.id)}
                      >
                        {loadingIds.includes(item.id) ? "Verifying..." : "Verify OTP"}
                      </button>
                      <button
                        className="px-3 py-1 bg-orange-500 text-white rounded-md"
                        disabled={otp.verified || loadingIds.includes(item.id)}
                        onClick={() => handleAction("resend_otp", item.id)}
                      >
                        {loadingIds.includes(item.id) ? "Resending..." : "Resend OTP"}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Order-level actions */}
      <div className="flex flex-col sm:flex-row gap-2 mt-3">
        {order.status === "failed" && (
          <button
            className="px-4 py-2 bg-green-500 text-white rounded-lg"
            disabled={loadingIds.includes(order.id)}
            onClick={() => handleAction("reschedule")}
          >
            {loadingIds.includes(order.id) ? "Rescheduling..." : "Reschedule Delivery"}
          </button>
        )}
        {order.status === "out_for_delivery" && (
          <button
            className="px-4 py-2 bg-red-500 text-white rounded-lg"
            disabled={loadingIds.includes(order.id)}
            onClick={() => handleAction("mark_failed")}
          >
            {loadingIds.includes(order.id) ? "Processing..." : "Mark Delivery Failed"}
          </button>
        )}
      </div>
    </motion.div>
  );
};

export default OrderCard;
