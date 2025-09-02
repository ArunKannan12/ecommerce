import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import axiosInstance from "../../api/axiosinstance";
import { useAuth } from "../../contexts/authContext";
import { motion } from "framer-motion";
import { CheckCircle, Clock, CreditCard, XCircle } from "lucide-react";

const OrderList = () => {
  const navigate = useNavigate();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      navigate("/login", { state: { from: "/orders" } });
      return;
    }

    const fetchOrders = async () => {
      setLoading(true);
      try {
        const res = await axiosInstance.get("orders/");
        const data = res.data.results || [];
        setOrders(data);
      } catch (error) {
        console.error("Failed to fetch orders:", error);
        toast.error(
          error.response?.data?.detail || "Failed to fetch your orders"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, [authLoading, isAuthenticated, navigate]);

  if (loading || authLoading)
    return <p className="p-6 text-center">Loading your orders...</p>;
  if (orders.length === 0)
    return <p className="p-6 text-center">You have no orders yet.</p>;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl sm:text-4xl font-extrabold mb-10 text-gray-900">
        Your Orders
      </h1>

      <motion.ul
        className="space-y-8"
        initial="hidden"
        animate="show"
        variants={{
          hidden: { opacity: 0 },
          show: {
            opacity: 1,
            transition: { staggerChildren: 0.12 },
          },
        }}
      >
        {orders.map((order) => {
          const items = order.items || [];
          const totalItems = items.length;

          const firstItem = items[0]?.product_variant;
          const displayName = firstItem
            ? `${firstItem.product_name}${
                firstItem.variant_name ? " - " + firstItem.variant_name : ""
              }${totalItems > 1 ? ` +${totalItems - 1} more` : ""}`
            : "Order";

          const images = items.slice(0, 3).map((item) => {
            const variant = item.product_variant;
            if (variant.images?.length) return variant.images[0].url;
            if (variant.product_images?.length) return variant.product_images[0];
            return "/placeholder.png";
          });

          const totalAmount = parseFloat(order.total);

          return (
            <motion.li
              key={order.id}
              variants={{
                hidden: { opacity: 0, y: 30 },
                show: { opacity: 1, y: 0 },
              }}
              className="bg-white/70 backdrop-blur-md shadow-xl rounded-2xl p-6 flex justify-between items-center hover:shadow-2xl transition border border-gray-100"
            >
              <div className="flex items-center space-x-6">
                {/* Product images */}
                <div className="flex -space-x-3">
                  {images.map((img, idx) => (
                    <motion.img
                      key={idx}
                      src={
                        img.startsWith("http")
                          ? img
                          : `http://localhost:8000${img}`
                      }
                      alt="Product"
                      className="w-16 h-16 object-cover rounded-xl border border-gray-200 shadow hover:scale-105 transition"
                      whileHover={{ scale: 1.08 }}
                    />
                  ))}
                  {totalItems > 3 && (
                    <span className="w-16 h-16 flex items-center justify-center bg-gray-100 rounded-xl text-sm font-medium text-gray-600 border border-gray-200">
                      +{totalItems - 3}
                    </span>
                  )}
                </div>

                {/* Order details */}
                <div>
                  <p className="font-semibold text-lg sm:text-xl text-gray-900 capitalize">
                    {displayName}
                  </p>
                  <p className="text-gray-500 text-sm">
                    Ordered on:{" "}
                    {new Date(order.created_at).toLocaleDateString(undefined, {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </p>
                  <p className="text-gray-600 text-sm font-medium">
                    Total: ₹{totalAmount.toFixed(2)}
                  </p>

                  {/* Status Badge */}
                  <p className="mt-3 flex items-center gap-2">
                    {order.status === "delivered" ? (
                      <span className="flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                        <CheckCircle size={16} /> Delivered
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm font-medium">
                        <Clock size={16} /> {order.status || "Processing"}
                      </span>
                    )}
                  </p>

                  {/* Payment Badge */}
                  <p className="mt-2 flex items-center gap-2">
                    {order.is_paid ? (
                      <span className="flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                        <CreditCard size={16} /> Paid
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium">
                        <XCircle size={16} /> Pending
                      </span>
                    )}
                  </p>
                </div>
              </div>

              {/* CTA Button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => navigate(`/orders/${order.id}`)}
                className="px-6 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-xl shadow-lg hover:from-blue-700 hover:to-indigo-700 transition"
              >
                View Details
              </motion.button>
            </motion.li>
          );
        })}
      </motion.ul>
    </div>
  );
};

export default OrderList;
