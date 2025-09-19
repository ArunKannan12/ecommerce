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

const stepIcons = {
  pending: "🕒",
  processing: "💳",
  packed: "📦",
  shipped: "🚚",
  out_for_delivery: "📍",
  delivered: "✅",
  cancelled: "❌",
  returned: "↩️",
  replacement: "🔁",
};

const OrderTracker = ({
  status,
  paymentMethod,
  timestamps = {},
  cancel_info,
  return_request,
  replacement_request,
}) => {
  const isCOD = paymentMethod?.toLowerCase() === "cod";
  const isCancelled = status?.toLowerCase() === "cancelled";

  const baseSteps = [
    { key: isCOD ? "pending" : "processing", label: isCOD ? "Pending" : "Processing" },
    { key: "packed", label: "Packed" },
    { key: "shipped", label: "Shipped" },
    { key: "out_for_delivery", label: "Out for Delivery" },
    { key: "delivered", label: "Delivered" },
  ];

  const postSteps = [];

  if (isCancelled) {
    baseSteps.splice(1);
    baseSteps.push({ key: "cancelled", label: "Cancelled", detached: false });
  }

  if (return_request?.status) {
    postSteps.push({
      key: "returned",
      label: "Return Requested",
      detached: true,
      status: return_request.status,
      finalized: return_request.status === "refunded",
    });
  }

  if (replacement_request?.status) {
    postSteps.push({
      key: "replacement",
      label: "Replacement Requested",
      detached: true,
      status: replacement_request.status,
      finalized: replacement_request.status === "shipped",
    });
  }

  const allSteps = [...baseSteps, ...postSteps];
  const currentStepIndex = allSteps.findIndex((s) => s.key === status?.toLowerCase());

  return (
    <div className="w-full px-4 py-6">
      <style>
        {`
          @keyframes verticalLine {
            from { height: 0%; }
            to { height: 100%; }
          }
          .animate-verticalLine {
            animation: verticalLine 1s ease-in-out forwards;
          }
        `}
      </style>

      <div className="flex flex-col gap-8 relative">
        {allSteps.map((step, idx) => {
          const isDetached = step.detached;
          const isCompleted = idx <= currentStepIndex && !isDetached && !isCancelled;
          const isCurrent = idx === currentStepIndex && !isDetached && !isCancelled;
          const timeText = formatRelativeTime(timestamps[step.key]);

          const isPostFinalized = step.finalized;
          const isPostPending = step.status && !step.finalized;

          const circleColor = isCancelled
            ? "bg-red-500 border-red-500 text-white"
            : isCompleted
            ? "bg-green-600 border-green-600 text-white"
            : isCurrent
            ? "bg-white border-blue-500 text-blue-600 animate-pulse"
            : isPostFinalized
            ? "bg-green-600 border-green-600 text-white"
            : isPostPending
            ? "bg-yellow-100 border-yellow-400 text-yellow-700"
            : "bg-white border-gray-300 text-gray-500";

          return (
            <div key={step.key} className="flex items-start gap-4 relative">
              {/* Connector Line */}
              {!isDetached && idx < allSteps.length - 1 && (
                <div className="absolute left-5 top-10 w-[2px] h-full z-0">
                  <div
                    className={`w-full ${
                      isCompleted ? "bg-green-500 animate-verticalLine" : "bg-gray-300"
                    } h-full rounded-full`}
                    style={{ animationDelay: `${idx * 0.2}s` }}
                  ></div>
                </div>
              )}

              {/* Step Circle */}
              <div
                className={`w-10 h-10 rounded-full border-2 flex items-center justify-center font-bold text-xl transition-all duration-500 ${circleColor}`}
              >
                {stepIcons[step.key] || "•"}
              </div>

              {/* Step Info */}
              <div className="flex flex-col pt-1">
                <p className={`text-sm font-semibold capitalize ${circleColor.includes("text-red") ? "text-red-600" : "text-gray-800"}`}>
                  {step.label}
                </p>
                {timeText && !isDetached && (
                  <p className="text-xs text-gray-500">{timeText}</p>
                )}

                {/* Cancel Info */}
                {step.key === "cancelled" && cancel_info && (
                  <div className="mt-1 text-xs text-gray-500 max-w-[200px]">
                    <p className="italic">{cancel_info.cancel_reason || "No reason provided"}</p>
                    <p>
                      {formatRelativeTime(cancel_info.cancelled_at)} <br />
                      <span className="font-medium">{cancel_info.cancelled_by_role}</span>
                    </p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default OrderTracker;