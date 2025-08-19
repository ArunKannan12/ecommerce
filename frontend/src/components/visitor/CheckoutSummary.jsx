import React from "react";

const CheckoutSummary = ({ totalAmount, onPlaceOrder }) => {
  return (
    <div className="mt-8 border-t pt-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Order Summary</h2>

      <div className="flex justify-between items-center mb-4">
        <span className="text-gray-600 text-sm">Subtotal</span>
        <span className="text-gray-800 font-medium text-sm">₹{totalAmount.toFixed(2)}</span>
      </div>

      {/* You can add shipping or tax rows here if needed */}
      {/* <div className="flex justify-between items-center mb-4">
        <span className="text-gray-600 text-sm">Shipping</span>
        <span className="text-gray-800 font-medium text-sm">₹0.00</span>
      </div> */}

      <div className="flex justify-between items-center border-t pt-4">
        <span className="text-lg font-semibold text-gray-700">Total</span>
        <span className="text-lg font-bold text-gray-900">₹{totalAmount.toFixed(2)}</span>
      </div>

      <button
        onClick={onPlaceOrder}
        className="mt-6 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded transition"
      >
        Place Order
      </button>
    </div>
  );
};

export default CheckoutSummary;