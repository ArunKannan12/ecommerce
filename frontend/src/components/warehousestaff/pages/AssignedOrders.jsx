import { useEffect, useState } from "react";
import axiosInstance from "../../../api/axiosinstance";
import { Spin, Tag, Card, Collapse } from "antd";
import {
  ClockCircleOutlined,
  EnvironmentOutlined,
  UserOutlined,
} from "@ant-design/icons";

const { Panel } = Collapse;

const statusColors = {
  pending: "default",
  processing: "orange",
  shipped: "blue",
  out_for_delivery: "cyan",
  delivered: "green",
  failed: "red",
};

const AssignedOrders = () => {
  const [assignedOrders, setAssignedOrders] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchAssignedOrders = async () => {
    setLoading(true);
    try {
      const res = await axiosInstance.get("warehouse/orders/assigned-orders/");
      setAssignedOrders(res.data.results || []);
    } catch (error) {
      console.error("Failed to fetch assigned orders", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssignedOrders();
  }, []);

  return (
    <div className="space-y-6">
      <Spin spinning={loading}>
        {assignedOrders.length === 0 ? (
          <div className="text-center text-gray-500 py-10 text-lg font-medium">
            No assigned orders found 🚚
          </div>
        ) : (
          assignedOrders.map((order) => (
            <Card
              key={order.id}
              className="border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden"
              title={
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-800 text-lg">
                      Order #{order.order_number}
                    </span>
                    <Tag color="blue" className="ml-1">
                      {order.status_display}
                    </Tag>
                  </div>
                  <div className="text-gray-500 text-sm flex items-center gap-1">
                    <ClockCircleOutlined />
                    {order.created_at_human}
                  </div>
                </div>
              }
            >
              {/* Main Grid */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* Customer & Delivery Info */}
                <div className="space-y-2">
                  <p className="text-sm text-gray-700">
                    <UserOutlined className="mr-2 text-gray-500" />
                    <strong>Customer:</strong> {order.customer}
                  </p>
                  <p className="text-sm text-gray-700">
                    <strong>Deliveryman:</strong> {order.deliveryman}
                  </p>
                  <p className="text-sm text-gray-700">
                    <strong>Payment:</strong> {order.payment_method}{" "}
                    {order.is_paid ? (
                      <Tag color="green" className="ml-1">
                        Paid
                      </Tag>
                    ) : (
                      <Tag color="red" className="ml-1">
                        Unpaid
                      </Tag>
                    )}
                  </p>
                  <p className="text-sm text-gray-700">
                    <strong>Total:</strong> ₹{order.total}
                  </p>
                </div>

                {/* Shipping Address */}
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <p className="text-gray-700 font-medium mb-1 flex items-center gap-1">
                    <EnvironmentOutlined /> Shipping Address
                  </p>
                  <p className="text-sm">
                    {order.shipping_address.full_name},{" "}
                    {order.shipping_address.phone_number}
                  </p>
                  <p className="text-sm text-gray-600">
                    {order.shipping_address.address},{" "}
                    {order.shipping_address.locality}, {order.shipping_address.city},{" "}
                    {order.shipping_address.district}
                  </p>
                  <p className="text-sm text-gray-600">
                    {order.shipping_address.state} - {order.shipping_address.postal_code},{" "}
                    {order.shipping_address.country}
                  </p>
                </div>
              </div>

              {/* Collapsible Order Items */}
              <div className="mt-4">
                <Collapse>
                  <Panel header={`Items (${order.total_items})`} key="items">
                    <div className="space-y-2">
                      {order.items.map((item) => (
                        <div
                          key={item.id}
                          className="flex flex-col sm:flex-row sm:items-center sm:justify-between bg-white border rounded-md p-3 hover:bg-gray-50 transition"
                        >
                          <div>
                            <p className="text-sm font-medium">{item.product}</p>
                            <p className="text-sm text-gray-600">
                              Qty: {item.quantity} | ₹{item.price}
                            </p>
                          </div>
                          <Tag color={statusColors[item.status] || "default"} className="mt-2 sm:mt-0">
                            {item.status.replace(/_/g, " ").toUpperCase()}
                          </Tag>
                        </div>
                      ))}
                    </div>
                  </Panel>
                </Collapse>
              </div>
            </Card>
          ))
        )}
      </Spin>
    </div>
  );
};

export default AssignedOrders;
