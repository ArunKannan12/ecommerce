import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import axiosInstance from "../../api/axiosinstance";
import { useAuth } from "../../contexts/AuthContext";

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
        toast.error(error.response?.data?.detail || "Failed to fetch your orders");
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, [authLoading, isAuthenticated, navigate]);

  if (loading || authLoading) return <p className="p-6 text-center">Loading your orders...</p>;
  if (orders.length === 0) return <p className="p-6 text-center">You have no orders yet.</p>;

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8 border-b pb-4">Your Orders</h1>
      <ul className="space-y-6">
        {orders.map((order) => {
          const items = order.items || [];
          const totalItems = items.length;

          // First item for display
          const firstItem = items[0]?.product_variant;

          // Display name: first item + "+N more" if multiple
          const displayName = firstItem
            ? `${firstItem.product_name}${firstItem.variant_name ? " - " + firstItem.variant_name : ""}${totalItems > 1 ? ` +${totalItems - 1} more` : ""}`
            : "Order";

          // Up to 3 images from each item's variant.images or product_images
          const images = items.slice(0, 3).map((item) => {
            const variant = item.product_variant;
            if (variant.images?.length) return variant.images[0].url;
            if (variant.product_images?.length) return variant.product_images[0];
            return "/placeholder.png";
          });

          // Total amount = sum(price * quantity)
          const totalAmount = items.reduce((sum, item) => sum + parseFloat(item.price) * item.quantity, 0);

          return (
            <li key={order.id} className="bg-white shadow-sm rounded-lg p-4 flex justify-between items-center hover:shadow-md transition">
              <div className="flex items-center space-x-6">
                <div className="flex -space-x-2">
                  {images.map((img, idx) => (
                    <img
                      key={idx}
                      src={img.startsWith("http") ? img : `http://localhost:8000${img}`}
                      alt="Product"
                      className="w-16 h-16 object-cover rounded border border-gray-200"
                    />
                  ))}
                  {totalItems > 3 && (
                    <span className="w-16 h-16 flex items-center justify-center bg-gray-200 rounded text-sm font-medium text-gray-600 border border-gray-300">
                      +{totalItems - 3}
                    </span>
                  )}
                </div>

                <div>
                  <p className="font-semibold text-lg text-gray-800">{displayName}</p>
                  <p className="text-gray-500 text-sm">
                    Ordered on: {new Date(order.created_at).toLocaleString()}
                  </p>
                  <p className="text-gray-500 text-sm">Total: ₹{totalAmount.toFixed(2)}</p>

                  <p className="mt-2">
                    <span
                      className={`inline-block px-2 py-1 rounded text-sm font-medium ${
                        order.status === "delivered" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"
                      }`}
                    >
                      Status: {order.status || "Processing"}
                    </span>
                  </p>

                  <p className="mt-1">
                    <span
                      className={`inline-block px-2 py-1 rounded text-sm font-medium ${
                        order.is_paid ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                      }`}
                    >
                      Payment: {order.is_paid ? "Paid" : "Pending"}
                    </span>
                  </p>
                </div>
              </div>

              <button
                onClick={() => navigate(`/orders/${order.id}`)}
                className="px-5 py-2 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition"
              >
                View Details
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export default OrderList;
