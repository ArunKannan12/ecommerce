import React from "react";

const CartShimmer = ({ count = 3 }) => {
  const shimmerStyle = {
    background: "linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%)",
    backgroundSize: "200% 100%",
    animation: "shimmer 1.5s infinite",
  };

  return (
    <div style={{ position: "relative" }}>
      <style>
        {`
          @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
          }
        `}
      </style>
      <div className="space-y-4">
        {[...Array(count)].map((_, i) => (
          <div
            key={i}
            style={{ border: "1px solid #d1d5db", borderRadius: "0.5rem", padding: "1rem" }}
            className="flex items-center gap-4"
          >
            {/* Image placeholder */}
            <div
              style={{ ...shimmerStyle, width: "5rem", height: "5rem", borderRadius: "0.375rem" }}
            ></div>

            {/* Content */}
            <div className="flex-1 space-y-3">
              <div style={{ ...shimmerStyle, width: "75%", height: "1.25rem", borderRadius: "0.25rem" }}></div>
              <div style={{ ...shimmerStyle, width: "50%", height: "1rem", borderRadius: "0.25rem" }}></div>

              {/* Quantity + Price */}
              <div className="flex items-center gap-4">
                <div style={{ ...shimmerStyle, width: "4rem", height: "1.5rem", borderRadius: "0.25rem" }}></div>
                <div style={{ ...shimmerStyle, width: "5rem", height: "1.5rem", borderRadius: "0.25rem" }}></div>
              </div>
            </div>

            {/* Remove button placeholder */}
            <div
              style={{ ...shimmerStyle, width: "2rem", height: "2rem", borderRadius: "9999px" }}
            ></div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CartShimmer;
