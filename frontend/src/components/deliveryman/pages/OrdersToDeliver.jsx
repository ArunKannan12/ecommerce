import React, { useEffect, useState } from "react";
import axiosInstance from "../../../api/axiosinstance";
import { motion, AnimatePresence } from "framer-motion";
import OrderCard from "./OrderCard";

const OrdersToDeliver = () => {
  const [ordersToDeliver, setOrdersToDeliver] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchOrdersToDeliver = async () => {
    setLoading(true);
    try {
      const res = await axiosInstance.get("deliveryman/orders/");
      setOrdersToDeliver(res.data.orders || []);
    } catch (error) {
      console.error("Error fetching orders:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrdersToDeliver();
  }, []);

  return (
    <div className="max-w-7xl py-10 px-10 space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">Orders to Deliver</h1>

      {loading && ordersToDeliver.length === 0 ? (
        <div className="text-center mt-10 text-gray-500">Loading orders...</div>
      ) : ordersToDeliver.length === 0 ? (
        <p className="text-gray-500 text-lg mt-6">No orders currently out for delivery.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          <AnimatePresence>
            {ordersToDeliver.map((order) => (
              <OrderCard
                key={order.id}
                order={order}
                refreshOrders={fetchOrdersToDeliver}
              />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};

export default OrdersToDeliver;
