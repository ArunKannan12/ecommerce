// src/components/helpers/OrderTracker.jsx
import React from "react";

const formatRelativeTime = (timestamp) => {
  if (!timestamp) return null;
  const now = new Date();
  const date = new Date(timestamp);
  const diffMs = now - date;

  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} min ago`;
  if (diffHours < 24) return `${diffHours} hr ago`;
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;

  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const OrderTracker = ({ status, timestamps = {}, cancel_info }) => {
  const steps = [
    { key: "pending", label: "Pending" },
    { key: "processing", label: "Processing" },
    { key: "shipped", label: "Shipped" },
    { key: "delivered", label: "Delivered" },
    { key: "cancelled", label: "Cancelled" },
  ];

  const isCancelled = status?.toLowerCase() === "cancelled";
  const currentStep = isCancelled
    ? steps.length - 1
    : steps.findIndex((s) => s.key === status?.toLowerCase());

  return (
    <div className="w-full px-4 py-6">
      <div className="flex flex-col lg:flex-row lg:items-center relative gap-8">
        {steps.map((step, idx) => {
          const isCompleted = idx < currentStep && !isCancelled;
          const isCurrent = idx === currentStep && !isCancelled;
          const timeText = formatRelativeTime(timestamps[step.key]);

          return (
            <div
              key={step.key}
              className="flex flex-col items-center relative lg:flex-1"
            >
              {/* Step circle */}
              <div
                className={`w-10 h-10 rounded-full border-2 flex items-center justify-center font-bold text-sm transition-all duration-500
                  ${isCancelled && step.key === "cancelled" ? "bg-red-500 border-red-500 text-white shadow-md" : ""}
                  ${isCompleted ? "bg-gradient-to-br from-green-400 to-green-600 border-green-600 text-white shadow-md" : ""}
                  ${isCurrent ? "border-green-500 text-green-600 bg-white shadow-sm animate-pulse" : ""}
                  ${!isCompleted && !isCurrent && !isCancelled ? "bg-white border-gray-300 text-gray-500" : ""}
                `}
              >
                {isCancelled && step.key === "cancelled" ? "✕" : idx + 1}
              </div>

              {/* Step label */}
              <p
                className={`mt-2 text-[11px] sm:text-xs font-semibold capitalize ${
                  isCancelled && step.key === "cancelled" ? "text-red-600" : ""
                }`}
              >
                {step.label}
              </p>

              {/* Timestamp */}
              {timeText && !isCancelled && (
                <p className="text-[9px] sm:text-[10px] text-gray-400">{timeText}</p>
              )}

              {/* Cancel info */}
              {isCancelled && cancel_info && step.key === "cancelled" && (
                <div className="mt-1 text-[9px] text-gray-400 text-center">
                  <p>{cancel_info.cancel_reason || "No reason provided"}</p>
                  <p>
                    {formatRelativeTime(cancel_info.cancelled_at)} by{" "}
                    {cancel_info.cancelled_by_role}
                  </p>
                </div>
              )}

              {/* Connector line */}
              {idx < steps.length - 1 && (
                <div
                  className={`absolute z-0 bg-gray-300 ${
                    isCompleted ? "bg-green-500" : ""
                  }
                  lg:w-full lg:h-[2px] lg:left-full lg:top-1/2
                  w-[2px] h-full top-full left-1/2 transform -translate-x-1/2 lg:translate-x-0`}
                ></div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default OrderTracker;