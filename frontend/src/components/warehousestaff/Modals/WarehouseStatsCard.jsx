import React from 'react'

const WarehouseStatsCard = ({ title, count, icon }) => {
  return (
    <div className="bg-white shadow rounded-lg p-4 flex items-center gap-4">
        <div className="text-indigo-600">{icon}</div>
        <div>
        <p className="text-sm text-gray-500">{title}</p>
        <p className="text-xl font-bold">{count}</p>
        </div>
    </div>
  )
}

export default WarehouseStatsCard