import React from "react";

const OrderSummary = ({ order, fetchOrder, canceling, onTriggerCancelModal, cancelLoading }) => {
  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 mb-10">
      <h2 className="text-2xl font-bold mb-4 text-gray-900 text-center">📦 Order Summary</h2>

      <div className="space-y-4 text-sm sm:text-base">
        <div className="flex justify-between">
          <span className="text-gray-500">Subtotal</span>
          <span className="font-medium text-gray-900">
            ₹{parseFloat(order.subtotal || 0).toFixed(2)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Delivery Charge</span>
          <span className="font-medium text-gray-900">
            ₹{parseFloat(order.delivery_charge || 0).toFixed(2)}
          </span>
        </div>
        <div className="flex justify-between border-t border-gray-200 pt-4 font-bold text-lg">
          <span className="text-gray-900">Total</span>
          <span className="text-gray-900">
            ₹{parseFloat(order.total || 0).toFixed(2)}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-500">Payment Method</span>
          <span className="font-medium text-gray-900">
            {order.payment_method || "Not selected"}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-500">Payment Status</span>
          <span
            className={`font-semibold ${
              order.is_paid ? "text-green-600" : "text-red-500"
            }`}
          >
            {order.is_paid ? "Paid" : "Pending"}
          </span>
        </div>
      </div>

      {/* Cancel button */}
      {!order.is_paid && !order.cancelled_at && (
        <div className="mt-6 text-center">
          <button
            disabled={canceling}
            onClick={onTriggerCancelModal}
            className="w-full sm:w-auto px-6 py-3 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition"
          >
            {cancelLoading ? "Cancelling..." : "Cancel Order"}
          </button>
        </div>
      )}
    </div>
  );
};

export default OrderSummary;