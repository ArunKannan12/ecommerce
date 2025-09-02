import React from "react";

const CheckoutSummary = ({ subtotal = 0, deliveryCharge = 0, totalAmount = 0, onPlaceOrder }) => {
  const safeSubtotal = Number(subtotal) || 0;
  const safeDelivery = Number(deliveryCharge) || 0;
  const safeTotal = Number(totalAmount) || 0;

  
  return (
    <div className="mt-8 border-t pt-6 px-4 pb-8 sm:px-6">
      <h2 className="text-xl font-semibold text-gray-800  mb-3">Order Summary</h2>

      {/* Subtotal */}
      <div className="flex justify-between items-center mb-4">
        <span className="text-gray-600 text-sm">Subtotal</span>
        <span className="text-gray-800 font-medium text-sm">₹{safeSubtotal.toFixed(2)}</span>
      </div>

      {/* Delivery Charge */}
      <div className="flex justify-between items-center mb-4">
        <span className="text-gray-600 text-sm">Delivery</span>
        <span className="text-gray-800 font-medium text-sm">₹{safeDelivery.toFixed(2)}</span>
      </div>

      {/* Total */}
      <div className="flex justify-between items-center border-t pt-4 mb-6">
        <span className="text-lg font-semibold text-gray-700">Total</span>
        <span className="text-lg font-bold text-gray-900">₹{safeTotal.toFixed(2)}</span>
      </div>

      {/* Place Order button */}
      <button
        onClick={onPlaceOrder}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded transition"
      >
        Place Order
      </button>
    </div>

  );
};

export default CheckoutSummary;
