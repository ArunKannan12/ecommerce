import React, { useState } from 'react';
import { ClipLoader } from 'react-spinners';

const LoadingShimmer = () => {
  const [loading, setLoading] = useState(false);

  const handleClick = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false); // stop loading after 3 seconds
    }, 3000);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <button
        onClick={handleClick}
        className="mb-4 px-4 py-2 bg-blue-500 text-white rounded"
      >
        Show Loading
      </button>

      {loading && <ClipLoader color="#1D4ED8" size={50} />}
    </div>
  );
};

export default LoadingShimmer;
