import React, { useEffect, useState } from "react";
import axiosInstance from "../../../api/axiosinstance";
import { Button, Select, Spin, Checkbox, message, Tabs } from "antd";
import { toast } from "react-toastify";
import AssignedOrders from "./AssignedOrders";

const OrderAssigning = () => {
  const [orders, setOrders] = useState([]);
  const [deliverymen, setDeliverymen] = useState([]);
  const [selectedOrders, setSelectedOrders] = useState([]);
  const [selectedDeliveryman, setSelectedDeliveryman] = useState(null);
  const [loadingOrders, setLoadingOrders] = useState(false);
  const [loadingDeliverymen, setLoadingDeliverymen] = useState(false);
  const [assignLoading, setAssignLoading] = useState(false);
  const [reloadAssigned, setReloadAssigned] = useState(false); // 👈 trigger re-fetch in AssignedOrders

  useEffect(() => {
    fetchOrders();
    fetchDeliverymen();
  }, []);

  const fetchOrders = async () => {
    setLoadingOrders(true);
    try {
      const res = await axiosInstance.get("warehouse/orders/unassigned-orders/");
      setOrders(res.data.results);
    } catch (err) {
      message.error(err.response?.data?.detail || "Failed to load orders");
    } finally {
      setLoadingOrders(false);
    }
  };

  const fetchDeliverymen = async () => {
    setLoadingDeliverymen(true);
    try {
      const res = await axiosInstance.get("warehouse/deliverymen/");
      setDeliverymen(res.data.results);
    } catch {
      message.error("Failed to load deliverymen");
    } finally {
      setLoadingDeliverymen(false);
    }
  };

  const toggleOrder = (orderNumber) =>
    setSelectedOrders((prev) =>
      prev.includes(orderNumber)
        ? prev.filter((o) => o !== orderNumber)
        : [...prev, orderNumber]
    );

  const handleAssign = async () => {
    if (!selectedDeliveryman || !selectedOrders.length)
      return message.warning("Select a deliveryman and at least one order.");

    setAssignLoading(true);
    try {
      const res = await axiosInstance.post("warehouse/orders/assign/deliveryman/", {
        order_numbers: selectedOrders,
        deliveryman_id: selectedDeliveryman,
      });
      toast.success(res.data.message);

      // Remove assigned orders from list
      setOrders((prev) => prev.filter((o) => !selectedOrders.includes(o.order_number)));
      setSelectedOrders([]);
      setSelectedDeliveryman(null);

      // ✅ trigger AssignedOrders re-fetch
      setReloadAssigned((prev) => !prev);

    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to assign orders");
    } finally {
      setAssignLoading(false);
    }
  };

  const items = [
    {
      key: "unassigned",
      label: "Unassigned Orders",
      children: (
        <>
          <div className="flex gap-3 items-center mb-4">
            <Select
              style={{ width: 250 }}
              placeholder="Select Deliveryman"
              value={selectedDeliveryman}
              loading={loadingDeliverymen}
              onChange={setSelectedDeliveryman}
              options={deliverymen.map((d) => ({
                label: `${d.full_name?.toUpperCase() || ""} (${d.email})`,
                value: d.id,
              }))}
            />
            <Button
              type="primary"
              loading={assignLoading}
              disabled={!selectedDeliveryman || !selectedOrders.length}
              onClick={handleAssign}
            >
              Assign {selectedOrders.length ? `(${selectedOrders.length}) Orders` : ""}
            </Button>
          </div>

          <Spin spinning={loadingOrders}>
            {orders.length === 0 ? (
              <div className="text-center text-gray-500 py-6">
                No unassigned orders.
              </div>
            ) : (
              orders.map((o) => (
                <div
                  key={o.id}
                  className={`border rounded p-3 flex justify-between items-center mb-2 transition-all ${
                    selectedOrders.includes(o.order_number)
                      ? "bg-blue-50 border-blue-400"
                      : "bg-white"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <Checkbox
                      checked={selectedOrders.includes(o.order_number)}
                      onChange={() => toggleOrder(o.order_number)}
                    />
                    <div>
                      <p className="font-medium">
                        Order #{o.order_number} — {o.customer}
                      </p>
                      <p className="text-sm text-gray-600">Total: ₹{o.total}</p>
                      <p className="text-xs inline-block px-1 rounded mt-1 bg-blue-100 text-blue-800">
                        {o.status_display}
                      </p>
                      {o.items.map((item) => (
                        <p key={item.id} className="text-sm text-gray-500">
                          {item.product} × {item.quantity}
                        </p>
                      ))}
                    </div>
                  </div>
                  <p className="text-gray-500 text-sm">
                    {new Date(o.created_at).toLocaleString()}
                  </p>
                </div>
              ))
            )}
          </Spin>
        </>
      ),
    },
    {
      key: "assigned",
      label: "Assigned Orders",
      children: <AssignedOrders reload={reloadAssigned} />, // 👈 use prop trigger
    },
  ];

  return (
    <div className="max-w-5xl mx-auto py-10 space-y-4">
      <h1 className="text-2xl font-semibold mb-4">Order Assignment</h1>
      <Tabs defaultActiveKey="unassigned" items={items} />
    </div>
  );
};

export default OrderAssigning;
