import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axiosInstance from "../../../api/axiosinstance";
import DeliverymanReturnShimmer from "../../../shimmer/DeliverymanReturnShimmer";
import DeliverymanReturnDetail from "./DeliverymanReturnDetail";

const DeliverymanReturns = () => {
  const [deliveryManReturns, setDeliveryManReturns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("pending");
  const [selectedReturnId, setSelectedReturnId] = useState(null);

  const fetchDeliveryManReturns = async () => {
    setLoading(true);
    try {
      const res = await axiosInstance.get("returns", {
        params: { status },
      });
      setDeliveryManReturns(res.data.results || []);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDeliveryManReturns();
  }, [status]);

  return (
    <div className="min-h-screen py-10 px-4 bg-gray-50">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-center">Return Requests</h1>

        {/* Status Tabs */}
        <div className="flex justify-center space-x-4 mb-6">
          {["pending", "collected"].map((tab) => (
            <button
              key={tab}
              className={`px-4 py-2 rounded-lg font-medium transition-colors duration-200 ${
                status === tab
                  ? "bg-yellow-500 text-white shadow-md"
                  : "bg-gray-200 hover:bg-gray-300"
              }`}
              onClick={() => setStatus(tab)}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Content */}
        {loading ? (
          <DeliverymanReturnShimmer />
        ) : deliveryManReturns.length === 0 ? (
          <p className="text-center text-gray-500 py-10">
            No return requests in this category.
          </p>
        ) : (
          <>
            {/* Table layout for large screens */}
            <div className="hidden lg:block overflow-x-auto">
              <table className="w-full table-auto border-gray-200 rounded-lg shadow-sm">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="px-4 py-2 text-left">Product</th>
                    <th className="px-4 py-2 text-left">Variant</th>
                    <th className="px-4 py-2 text-left">Quantity</th>
                    <th className="px-4 py-2 text-left">Reason</th>
                    <th className="px-4 py-2 text-left">Status</th>
                  </tr>
                </thead>
                <tbody>
                  <AnimatePresence>
                    {deliveryManReturns.map((ret) => (
                      <motion.tr
                        key={ret.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.3 }}
                        className="border-b border-gray-200 hover:bg-gray-50 cursor-pointer"
                        onClick={() => setSelectedReturnId(ret.id)}
                      >
                        <td className="px-4 py-2">{ret.product}</td>
                        <td className="px-4 py-2">{ret.variant || "-"}</td>
                        <td className="px-4 py-2">{ret.order_item?.quantity || "-"}</td>
                        <td className="px-4 py-2">{ret.reason}</td>
                        <td className="px-4 py-2">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-semibold ${
                              ret.status === "pending"
                                ? "bg-yellow-500 text-white"
                                : "bg-green-600 text-white"
                            }`}
                          >
                            {ret.status.toUpperCase()}
                          </span>
                        </td>
                      </motion.tr>
                    ))}
                  </AnimatePresence>
                </tbody>
              </table>
            </div>

            {/* Card layout for mobile/tablet */}
            <div className="flex flex-wrap justify-center gap-4 lg:hidden">
              <AnimatePresence>
                {deliveryManReturns.map((ret) => (
                  <motion.div
                    key={ret.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                    className="p-4 rounded-lg shadow-sm w-80 bg-white hover:shadow-lg transition-shadow cursor-pointer"
                    onClick={() => setSelectedReturnId(ret.id)}
                  >
                    <p className="font-semibold">{ret.product}</p>
                    {ret.variant && (
                      <p className="text-sm text-gray-600">Variant: {ret.variant}</p>
                    )}
                    <p className="text-sm text-gray-600">
                      Qty: {ret.order_item?.quantity}
                    </p>
                    <p className="text-sm text-gray-600">Reason: {ret.reason}</p>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-semibold mt-2 inline-block ${
                        ret.status === "pending"
                          ? "bg-yellow-500 text-white"
                          : "bg-green-600 text-white"
                      }`}
                    >
                      {ret.status.toUpperCase()}
                    </span>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </>
        )}

        {/* Modal for Return Detail */}
        {selectedReturnId && (
          <DeliverymanReturnDetail
            returnId={selectedReturnId}
            onClose={() => setSelectedReturnId(null)}
            onUpdated={fetchDeliveryManReturns} // optional: refresh after update
          />
        )}
      </div>
    </div>
  );
};

export default DeliverymanReturns;
