import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import axiosInstance from "../../../api/axiosinstance";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const DeliveryManDashboardHome = () => {
  const [profile, setProfile] = useState({
    name: "",
    phone: "",
    vehicle_number: "",
    joined_at: "",
    total_deliveries: 0
  });

  const [stats, setStats] = useState({
    active_deliveries: 0,
    completed_deliveries: 0,
    failed_deliveries: 0,
    pending_otp_verification: 0,
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const res = await axiosInstance.get("deliveryman/dashboard/"); // Adjust URL if needed
        setProfile(res.data.profile);
        setStats(res.data.stats);
        console.log("Dashboard Data:", res.data);
      } catch (error) {
        console.error("Error loading dashboard:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  const chartData = [
    { name: "Active", value: stats.active_deliveries },
    { name: "Completed", value: stats.completed_deliveries },
    { name: "Failed", value: stats.failed_deliveries },
    { name: "Pending OTP", value: stats.pending_otp_verification },
  ];

  if (loading) return <div className="text-center mt-10">Loading...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-700">Delivery Dashboard</h1>

      {/* Profile Info */}
      <div className="bg-white p-6 rounded-xl shadow-md">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">Profile Information</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-gray-700">
          <div><strong>Name:</strong> {profile.name}</div>
          <div><strong>Phone:</strong> {profile.phone}</div>
          <div><strong>Vehicle:</strong> {profile.vehicle_number}</div>
          <div><strong>Joined:</strong> {new Date(profile.joined_at).toLocaleDateString()}</div>
          <div><strong>Total Deliveries:</strong> {profile.total_deliveries}</div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
        {[
          { label: "Active Deliveries", value: stats.active_deliveries, color: "bg-blue-500" },
          { label: "Completed Deliveries", value: stats.completed_deliveries, color: "bg-green-500" },
          { label: "Failed Deliveries", value: stats.failed_deliveries, color: "bg-red-500" },
          { label: "Pending OTP", value: stats.pending_otp_verification, color: "bg-yellow-500" },
        ].map((stat) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className={`p-6 rounded-xl shadow-lg ${stat.color} text-white flex flex-col items-center justify-center`}
          >
            <h2 className="text-xl font-semibold">{stat.label}</h2>
            <p className="text-3xl font-bold mt-2">{stat.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Delivery Chart */}
      <div className="bg-white p-6 rounded-xl shadow-lg">
        <h2 className="text-lg font-semibold mb-4">Delivery Overview</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <XAxis dataKey="name" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="value" fill="#22c55e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default DeliveryManDashboardHome;
