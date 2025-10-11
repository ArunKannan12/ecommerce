import React, { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axiosInstance from "../../../api/axiosinstance";
import { toast } from "react-toastify";

const STATUSES = ["All", "Pending", "Picked", "Packed", "Shipped", "Out for Delivery"];
const STATUS_STAGES = ["pending", "picked", "packed", "shipped", "out_for_delivery"];

const STATUS_COLORS = {
  pending: "bg-yellow-100 text-yellow-800",
  picked: "bg-blue-100 text-blue-800",
  packed: "bg-purple-100 text-purple-800",
  shipped: "bg-green-100 text-green-800",
  out_for_delivery: "bg-orange-100 text-orange-800",
  cancelled: "bg-gray-100 text-gray-700",
};

function WarehouseOrders() {
  const [items, setItems] = useState([]);
  const [ordersMap, setOrdersMap] = useState({});
  const [expandedOrders, setExpandedOrders] = useState({});
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("All");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [nextPage, setNextPage] = useState(null);
  const [previousPage, setPreviousPage] = useState(null);

  const toggleExpand = (orderNumber) => {
    setExpandedOrders((prev) => ({ ...prev, [orderNumber]: !prev[orderNumber] }));
  };

  const getNextAction = (item) => {
    if (item.status === "pending") return "pick";
    if (item.status === "picked") return "pack";
    if (item.status === "packed") return "ship";
    return null;
  };

  const truncateText = (text, maxLength = 30) => {
    return text.length > maxLength ? text.slice(0, maxLength) + "..." : text;
  };

  const handleNextAction = async (item) => {
    const action = getNextAction(item);
    if (!action) return;

    try {
      await axiosInstance.post(`warehouse/items/${item.id}/${action}/`);
      toast.success(`${truncateText(item.product)} marked as ${action}ed`);
      fetchItems();
    } catch (err) {
      console.error(err);
      toast.error("Failed to update item status");
    }
  };

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page };
      if (status !== "All") params.status = status.toLowerCase().replace(/\s/g, "_");
      if (search) params.product = search;

      const res = await axiosInstance.get("order-items/status/", { params });
      setItems(res.data.results || []);
      setNextPage(res.data.next);
      setPreviousPage(res.data.previous);

      // Group items by order_number
      const map = {};
      (res.data.results || []).forEach((item) => {
        if (!map[item.order_number]) map[item.order_number] = [];
        map[item.order_number].push(item);
      });
      setOrdersMap(map);
    } catch (err) {
      console.error(err);
      toast.error("Failed to load items");
    } finally {
      setLoading(false);
    }
  }, [page, status, search]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
      fetchItems();
    }, 500);
    return () => clearTimeout(timer);
  }, [search, fetchItems]);

  const getProgressWidth = (status) => {
    const index = STATUS_STAGES.indexOf(status);
    return ((index + 1) / STATUS_STAGES.length) * 100;
  };

  return (
    <div className="max-w-7xl mx-auto py-10 px-4 space-y-6">
      <motion.h1
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="text-3xl font-semibold mb-6 text-gray-800"
      >
        Warehouse Orders
      </motion.h1>

      {/* Filters */}
      <div className="flex flex-col md:flex-row md:items-center md:space-x-4 space-y-2 md:space-y-0 mb-6">
        <input
          type="text"
          placeholder="Search by product..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-4 py-2 border rounded-lg flex-1 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="px-4 py-2 border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {/* Loading / Empty */}
      {loading ? (
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-gray-500 text-center">
          Loading items...
        </motion.p>
      ) : Object.keys(ordersMap).length === 0 ? (
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-gray-500 text-center">
          No orders found.
        </motion.p>
      ) : (
        <div className="space-y-4">
          {Object.keys(ordersMap).map((orderNumber) => {
            const orderItems = ordersMap[orderNumber];
            const isExpanded = expandedOrders[orderNumber] || false;
            const customer = orderItems[0]?.customer;

            return (
              <motion.div
                key={orderNumber}
                layout
                className="bg-white rounded-2xl shadow-md p-5 border border-gray-100 hover:shadow-lg transition"
              >
                {/* Order Header */}
                <div
                  className="flex flex-col md:flex-row justify-between items-start md:items-center cursor-pointer"
                  onClick={() => toggleExpand(orderNumber)}
                >
                  <div className="flex flex-col md:flex-row items-start md:items-center space-y-1 md:space-y-0 md:space-x-2 w-full md:w-auto">
                    <span className="font-medium text-gray-800 truncate max-w-[200px] md:max-w-xs">
                      Order #{orderNumber}
                    </span>
                    <span className="text-gray-500 truncate max-w-[150px] md:max-w-xs">
                      ({truncateText(customer, 20)})
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-700 text-xs font-medium">
                      {orderItems.length} item{orderItems.length > 1 ? "s" : ""}
                    </span>
                  </div>
                  <svg
                    className={`w-5 h-5 text-gray-500 transition-transform mt-2 md:mt-0 ${isExpanded ? "rotate-180" : ""}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>

                {/* Order Items */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                      className="mt-4 space-y-3 border-t border-gray-100 pt-3"
                    >
                      {orderItems.map((item) => {
                        const nextAction = getNextAction(item);
                        const progressWidth = getProgressWidth(item.status);

                        return (
                          <div
                            key={item.id}
                            className="flex flex-col md:flex-row justify-between items-start md:items-center bg-gray-50 rounded-lg p-3 shadow-sm hover:shadow-md transition space-y-2 md:space-y-0"
                          >
                            <div className="flex-1 w-full">
                              <span className="font-medium text-gray-800 truncate block max-w-full">
                                {truncateText(item.product)}
                              </span>
                              <span className="ml-1 text-gray-500">({item.quantity}x)</span>
                              <span
                                className={`ml-2 px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[item.status]}`}
                              >
                                {item.status.replace("_", " ")}
                              </span>

                              {/* Progress Bar */}
                              <div className="mt-2 w-full bg-gray-200 h-2 rounded-full overflow-hidden">
                                <div
                                  className="h-2 bg-blue-600 rounded-full transition-all duration-300"
                                  style={{ width: `${progressWidth}%` }}
                                />
                              </div>
                              <div className="flex justify-between text-xs text-gray-400 mt-1">
                                {STATUS_STAGES.map((stage) => (
                                  <span key={stage} className="truncate">{stage.replace("_", " ")}</span>
                                ))}
                              </div>
                            </div>

                            {nextAction && (
                              <button
                                onClick={() => handleNextAction(item)}
                                className="mt-2 md:mt-0 px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition whitespace-nowrap"
                              >
                                {nextAction}
                              </button>
                            )}
                          </div>
                        );
                      })}
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}

          {/* Pagination */}
          <div className="flex flex-col md:flex-row justify-between mt-4 space-y-2 md:space-y-0">
            <button
              disabled={!previousPage}
              onClick={() => setPage((p) => Math.max(p - 1, 1))}
              className="px-4 py-2 bg-gray-200 rounded-lg disabled:opacity-50 hover:bg-gray-300 transition"
            >
              Previous
            </button>
            <span className="text-gray-700 font-medium text-center">Page {page}</span>
            <button
              disabled={!nextPage}
              onClick={() => setPage((p) => p + 1)}
              className="px-4 py-2 bg-gray-200 rounded-lg disabled:opacity-50 hover:bg-gray-300 transition"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default WarehouseOrders;
