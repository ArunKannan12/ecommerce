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
        const data = res.data.results || []
        console.log('oders data',data);
        
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
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Your Orders</h1>
      <ul className="divide-y">
        {orders.map((order) => {
          console.log(orders);
          
          const totalAmount = (order.items || []).reduce(
            (acc, item) => acc + (item.price || 0) * (item.quantity || 1),
            0
          );

          return (
            <li
              key={order.id}
              className="py-4 flex justify-between items-center border-b"
            >
              <div>
                <p className="font-semibold">Order #{order.id}</p>
                <p className="text-sm text-gray-500">
                  {new Date(order.created_at).toLocaleString()}
                </p>
                <p className="text-sm text-gray-500">
                  Total: ₹{totalAmount.toFixed(2)}
                </p>
                <p className="text-sm">
                  Status:{" "}
                  <span
                    className={
                      order.status === "delivered"
                        ? "text-green-600"
                        : "text-yellow-600"
                    }
                  >
                    {order.status || "Processing"}
                  </span>
                </p>
                <p className="text-sm">
                  Payment:{" "}
                  <span
                    className={order.is_paid ? "text-green-600" : "text-red-600"}
                  >
                    {order.is_paid ? "Paid" : "Pending"}
                  </span>
                </p>
              </div>
              <button
                onClick={() => navigate(`/orders/${order.id}`)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
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
