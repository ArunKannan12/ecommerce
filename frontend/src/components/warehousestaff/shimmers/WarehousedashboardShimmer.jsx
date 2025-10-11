import React from 'react'
import { motion } from "framer-motion";

const ShimmerCard = () => (
  <motion.div
    className="bg-gray-200 rounded-xl h-24 animate-pulse"
    initial={{ opacity: 0.5 }}
    animate={{ opacity: 1 }}
    transition={{ repeat: Infinity, repeatType: "reverse", duration: 1.2 }}
  />
);
const ShimmerLineChart = () => (
  <motion.div
    className="bg-gray-200 rounded-lg h-64 w-full animate-pulse"
    initial={{ opacity: 0.5 }}
    animate={{ opacity: 1 }}
    transition={{ repeat: Infinity, repeatType: "reverse", duration: 1.2 }}
  />
);
const WarehousedashboardShimmer = () => {
  return (
    <div className="max-w-7xl mx-auto py-6 px-4 space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
        {Array(5).fill(0).map((_, idx) => (
          <ShimmerCard key={idx} />
        ))}
      </div>

      {/* Recent Returns */}
      <div className="bg-white rounded-lg shadow p-4 space-y-2">
        <div className="h-6 w-48 bg-gray-200 rounded animate-pulse" />
        {Array(3).fill(0).map((_, idx) => (
          <div key={idx} className="h-4 bg-gray-200 rounded animate-pulse w-full" />
        ))}
      </div>

      {/* Recent Replacements */}
      <div className="bg-white rounded-lg shadow p-4 space-y-2">
        <div className="h-6 w-56 bg-gray-200 rounded animate-pulse" />
        {Array(3).fill(0).map((_, idx) => (
          <div key={idx} className="h-4 bg-gray-200 rounded animate-pulse w-full" />
        ))}
      </div>

      {/* Trends Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Array(5).fill(0).map((_, idx) => (
          <ShimmerLineChart key={idx} />
        ))}
      </div>
    </div>
  )
}

export default WarehousedashboardShimmer