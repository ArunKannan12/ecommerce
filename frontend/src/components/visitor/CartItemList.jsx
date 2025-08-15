import React from "react";

const CartItemList = ({ cartItems, isAuthenticated }) => {
  if (!cartItems.length) return <p className="text-gray-500">Your cart is empty.</p>;

  return (
    <ul className="divide-y mb-6">
      {cartItems.map((item) => {
        const variant = isAuthenticated ? item.product_variant_detail || {} : item || {};
        const quantity = item?.quantity || 1;
        const productName = variant?.product_name || "Unknown Product";
        const variantName = variant?.variant_name || "";
        const price = variant?.price || item?.price || 0;

        const imageUrl =
          variant.images?.[0]?.image_url ||
          (variant.product_images?.[0] &&
            `http://localhost:8000${variant.product_images[0]}`) ||
          "/placeholder.png";

        return (
          <li key={variant?.id || Math.random()} className="py-4 flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <img
                src={imageUrl}
                alt={productName}
                className="w-20 h-20 object-cover rounded-md"
              />
              <div>
                <p className="font-semibold">{productName} - {variantName}</p>
                <p className="text-sm text-gray-500">Qty: {quantity}</p>
              </div>
            </div>
            <p className="text-gray-800 font-medium">₹{(price * quantity).toFixed(2)}</p>
          </li>
        );
      })}
    </ul>
  );
};

export default CartItemList;
