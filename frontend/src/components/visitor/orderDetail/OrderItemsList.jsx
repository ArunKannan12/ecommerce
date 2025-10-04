import React from "react";
import { motion } from "framer-motion";

const fadeUp = {
  hidden: { opacity: 0, y: 10 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    transition: {
      delay: i * 0.05,
      duration: 0.3,
      ease: "easeOut",
    },
  }),
};

const OrderItemsList = ({ items }) => {
  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 mb-10">
      <h2 className="text-2xl font-bold mb-6 text-gray-900 text-center">🛍️ Order Items</h2>

      <motion.div
        initial="hidden"
        animate="visible"
        variants={{
          hidden: {},
          visible: {
            transition: {
              staggerChildren: 0.05,
            },
          },
        }}
        className="divide-y divide-gray-200"
      >
        {items.map((item, index) => {
          const variant = item.product_variant;
          const quantity = item.quantity || 1;
          const price = parseFloat(item.price || variant.final_price || 0);
          const imageUrl =
            variant.images?.[0]?.image_url ||
            variant.primary_image_url ||
            "/placeholder.png";

          return (
            <motion.div
              key={item.id}
              custom={index}
              variants={fadeUp}
              className="py-4 flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4"
            >
              {/* Left: Image + Name */}
              <div className="flex items-center gap-4">
                <img
                  src={imageUrl}
                  alt={variant.product_name}
                  className="w-14 h-14 object-cover rounded-md"
                />
                <div>
                  <p className="font-medium text-gray-900">
                    {variant.product_name}
                    {variant.variant_name && (
                      <span className="text-sm text-gray-600"> – {variant.variant_name}</span>
                    )}
                  </p>
                  <p className="text-sm text-gray-500">Qty: {quantity}</p>
                </div>
              </div>

              {/* Right: Status + Price */}
              <div className="flex flex-col sm:items-end text-sm text-gray-700 gap-1">
                <div>
                  {variant.allow_return && item.return_remaining_days > 0 ? (
                    <span className="text-yellow-700">
                      🔄 {item.return_remaining_days} day{item.return_remaining_days !== 1 && "s"}
                    </span>
                  ) : (
                    <span className="text-gray-400">No Return</span>
                  )}
                </div>
                <div>
                  {variant.allow_replacement && item.replacement_remaining_days > 0 ? (
                    <span className="text-indigo-700">
                      ♻️ {item.replacement_remaining_days} day{item.replacement_remaining_days !== 1 && "s"}
                    </span>
                  ) : (
                    <span className="text-gray-400">No Replacement</span>
                  )}
                </div>
                <div className="font-bold text-gray-900">
                  ₹{(price * quantity).toFixed(2)}
                  <span className="block text-xs text-gray-500 font-normal">
                    ₹{price.toFixed(2)} × {quantity}
                  </span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
};

export default OrderItemsList;