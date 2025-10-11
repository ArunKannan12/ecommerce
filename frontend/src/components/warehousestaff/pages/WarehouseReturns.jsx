import React, { useEffect, useState } from "react";
import axiosInstance from "../../../api/axiosinstance";
import { Spin, Input, Select, Button, Table } from "antd";

const { Option } = Select;

const WarehouseReturns = () => {
  const [returns, setReturns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [nextPage, setNextPage] = useState(null);
  const [previousPage, setPreviousPage] = useState(null);

  const fetchReturns = async () => {
    setLoading(true);
    try {
      const params = { page };
      if (status) params.status = status;
      if (search) params.search = search;

      const res = await axiosInstance.get("returns/", { params });
      setReturns(res.data.results || []);
      setNextPage(res.data.next);
      setPreviousPage(res.data.previous);
    } catch (error) {
      console.error("Error fetching returns:", error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch on page or status change
  useEffect(() => {
    fetchReturns();
  }, [page, status]);

  // Debounced search effect
  useEffect(() => {
    const handler = setTimeout(() => {
      setPage(1);
      fetchReturns();
    }, 500);

    return () => clearTimeout(handler);
  }, [search]);

  // Table columns for clarity
  const columns = [
    {
      title: "Return ID",
      dataIndex: "id",
      key: "id",
    },
    {
      title: "Order Number",
      dataIndex: ["order", "order_number"],
      key: "order_number",
    },
    {
      title: "Product",
      dataIndex: ["order_item", "product_name"],
      key: "product_name",
    },
    {
      title: "Reason",
      dataIndex: "reason",
      key: "reason",
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
    },
    {
      title: "Created At",
      dataIndex: "created_at",
      key: "created_at",
      render: (text) => new Date(text).toLocaleString(),
    },
  ];

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-4">Warehouse Return Requests</h2>

      {/* --- Filters --- */}
      <div className="flex flex-wrap gap-3 mb-4">
        <Input
          placeholder="Search by order number..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 240 }}
        />
        <Select
          placeholder="Filter by status"
          value={status}
          onChange={(val) => setStatus(val)}
          style={{ width: 200 }}
          allowClear
        >
          <Option value="pending">Pending</Option>
          <Option value="approved">Approved</Option>
          <Option value="rejected">Rejected</Option>
          <Option value="refunded">Refunded</Option>
        </Select>
      </div>

      {/* --- Table --- */}
      {loading ? (
        <div className="flex justify-center py-10">
          <Spin size="large" />
        </div>
      ) : (
        <Table
          dataSource={returns}
          columns={columns}
          rowKey="id"
          pagination={false}
        />
      )}

      {/* --- Pagination --- */}
      <div className="flex justify-between items-center mt-4">
        <Button
          disabled={!previousPage}
          onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
        >
          Previous
        </Button>
        <span>Page {page}</span>
        <Button
          disabled={!nextPage}
          onClick={() => setPage((prev) => prev + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
};

export default WarehouseReturns;
