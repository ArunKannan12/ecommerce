import React, { useEffect, useState } from "react";
import axiosInstance from "../../../api/axiosinstance";
import { motion, AnimatePresence } from "framer-motion";
import OrderCard from "./OrderCard";

const OrdersToDeliver = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("out_for_delivery");

  const fetchOrders = async () => {
    setLoading(true);
    try {
      let statusQuery = "out_for_delivery,failed";
      if (activeTab === "completed") statusQuery = "delivered";
      else if (activeTab === "failed") statusQuery = "failed";

      const res = await axiosInstance.get(`deliveryman/orders/?status=${statusQuery}`);
      setOrders(res.data.orders || []);
    } catch (error) {
      console.error("Error fetching orders:", error);
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    fetchOrders();
  }, [activeTab]);

    const filteredOrders = orders.filter(order =>
      activeTab === "pending" ? order.status === "out_for_delivery" :
      activeTab === "completed" ? order.status === "delivered" :
      activeTab === "failed" ? order.status === "failed" : false
    );
    console.log(orders);
    

   return (
    <div className="max-w-7xl py-10 px-10">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">My Deliveries</h1>

      <div className="flex space-x-4 mb-6">
        {["pending", "completed", "failed"].map(tab => (
          <button
            key={tab}
            className={`px-4 py-2 rounded-lg ${
              activeTab === tab ? "bg-yellow-500 text-white" : "bg-gray-200"
            }`}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-center py-10 text-gray-500">Loading orders...</p>
      ) : filteredOrders.length === 0 ? (
        <p className="text-center py-10 text-gray-500">No orders in this category.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          <AnimatePresence>
            {filteredOrders.map(order => (
              <OrderCard key={order.id} order={order} refreshOrders={() => {}} />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};

export default OrdersToDeliver;
