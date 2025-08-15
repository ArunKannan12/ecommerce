import React from "react";

const CheckoutSummary = ({ totalAmount, onPlaceOrder }) => {
  return (
    <div className="mt-6 flex justify-between items-center">
      <p className="text-xl font-bold">Total: ₹{totalAmount.toFixed(2)}</p>
      <button
        onClick={onPlaceOrder}
        className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700"
      >
        Place Order
      </button>
    </div>
  );
};

export default CheckoutSummary;
