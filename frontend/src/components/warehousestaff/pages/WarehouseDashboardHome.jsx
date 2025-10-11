import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { Package, Box, Truck, Repeat } from 'lucide-react';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from 'recharts';
import axiosInstance from '../../../api/axiosinstance';
import WarehousedashboardShimmer from '../shimmers/WarehousedashboardShimmer';
import { Tab } from '@headlessui/react';

// ---------------- KPI Card ----------------
const WarehouseStatsCard = ({ title, count, icon, sparklineData }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.4 }}
    whileHover={{ scale: 1.03 }}
    className="bg-white shadow-md rounded-xl p-4 flex flex-col gap-2 hover:shadow-lg transition-shadow"
  >
    <div className="flex items-center gap-3">
      <div className="text-indigo-600">{icon}</div>
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <p className="text-2xl font-semibold text-gray-800">{count}</p>
      </div>
    </div>
    {sparklineData && sparklineData.length > 0 && (
      <ResponsiveContainer width="100%" height={30}>
        <LineChart data={sparklineData}>
          <Line type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    )}
  </motion.div>
);

// ---------------- Collapsible List Item ----------------
const CollapsibleOrderItem = ({ order }) => (
  <details className="border rounded p-3 hover:shadow-sm transition-shadow">
    <summary className="flex justify-between cursor-pointer font-medium text-gray-700">
      <span>Order #{order.order_number}</span>
      <span className="text-indigo-600">{order.status}</span>
    </summary>
    <div className="mt-2 space-y-1">
      {order.items.map((item) => (
        <p key={item.id} className="text-sm text-gray-600">
          {item.product} × {item.quantity}
        </p>
      ))}
    </div>
  </details>
);

// ---------------- Warehouse Dashboard Home ----------------
const WarehouseDashboardHome = () => {
  const [stats, setStats] = useState(null);
  const [returns, setReturns] = useState([]);
  const [replacements, setReplacements] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('orders');

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const statsRes = await axiosInstance.get('/warehouse/stats/');
      setStats(statsRes.data);

      const returnsRes = await axiosInstance.get('/returns/?status=pending');
      setReturns(returnsRes.data.results);

      const replacementsRes = await axiosInstance.get('/replacements/?status=pending');
      setReplacements(replacementsRes.data.results);
    } catch (error) {
      const errMsg = error.response?.data?.detail || "Failed to load warehouse data";
      toast.error(errMsg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading || !stats) return <WarehousedashboardShimmer />;

  const mergeTrends = (key) => stats.trends[key].map((item) => ({ date: item.date, count: item.count }));

  const kpis = [
    { title: 'Pending Orders', key: 'orders', count: stats.overall.pending_orders, icon: <Package size={24} /> },
    { title: 'Picked Items', key: 'picked_items', count: stats.overall.picked_items, icon: <Box size={24} /> },
    { title: 'Packed Items', key: 'packed_items', count: stats.overall.packed_items, icon: <Box size={24} /> },
    { title: 'Shipped Items', key: 'shipped_items', count: stats.overall.shipped_items, icon: <Truck size={24} /> },
    { title: 'Assigned Orders', key: 'assigned_orders', count: stats.overall.assigned_orders, icon: <Truck size={24} /> },
  ];

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 space-y-6">
      {/* ---------------- KPI Cards ---------------- */}
      <motion.div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {kpis.map((k) => (
          <WarehouseStatsCard key={k.key} title={k.title} count={k.count} icon={k.icon} sparklineData={mergeTrends(k.key)} />
        ))}
      </motion.div>

      {/* ---------------- Returns & Replacements ---------------- */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <motion.div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-lg font-semibold mb-3">Pending Return Requests</h3>
          {returns.length === 0 ? (
            <p className="text-gray-500">No pending returns</p>
          ) : (
            <div className="space-y-2">
              {returns.map((r) => <CollapsibleOrderItem key={r.id} order={r.order} />)}
            </div>
          )}
        </motion.div>

        <motion.div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-lg font-semibold mb-3">Pending Replacement Requests</h3>
          {replacements.length === 0 ? (
            <p className="text-gray-500">No pending replacements</p>
          ) : (
            <div className="space-y-2">
              {replacements.map((r) => <CollapsibleOrderItem key={r.id} order={r.order} />)}
            </div>
          )}
        </motion.div>
      </div>

      {/* ---------------- Trend Charts (Tabbed) ---------------- */}
      <Tab.Group selectedIndex={['orders','picked_items','packed_items','shipped_items','assigned_orders'].indexOf(activeTab)} onChange={index => setActiveTab(kpis[index].key)}>
        <Tab.List className="flex space-x-2 bg-gray-50 p-2 rounded">
          {kpis.map((k) => (
            <Tab key={k.key} className={({ selected }) => `px-3 py-1 rounded font-medium ${selected ? 'bg-indigo-600 text-white' : 'text-gray-700'}`}>
              {k.title}
            </Tab>
          ))}
        </Tab.List>
        <Tab.Panels className="mt-4">
          {kpis.map((k) => {
            const data = mergeTrends(k.key);
            return (
              <Tab.Panel key={k.key}>
                {data.length === 0 ? (
                  <p className="text-gray-500">No trend data</p>
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={data}>
                      <defs>
                        <linearGradient id={`lineGradient-${k.key}`} x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#6366f1" stopOpacity={0.8} />
                          <stop offset="100%" stopColor="#6366f1" stopOpacity={0.2} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis allowDecimals={false} />
                      <Tooltip content={({ active, payload, label }) => active && payload ? (
                        <div className="bg-white p-2 rounded shadow text-sm">
                          <p className="font-semibold">{label}</p>
                          <p>{payload[0].value} items</p>
                        </div>
                      ) : null} />
                      <Line type="monotone" dataKey="count" stroke={`url(#lineGradient-${k.key})`} strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </Tab.Panel>
            );
          })}
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
};

export default WarehouseDashboardHome;
