import React from 'react';

const shimmerStyle = {
  background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 37%, #f0f0f0 63%)',
  backgroundSize: '400% 100%',
  animation: 'shimmer 1.5s ease-in-out infinite',
};

const ShimmerCard = () => (
  <div className="border rounded-lg p-6">
    <div
      style={shimmerStyle}
      className="h-32 rounded mb-4"
    ></div>
    <div
      style={shimmerStyle}
      className="h-6 rounded w-3/4 mx-auto"
    ></div>
  </div>
);

// Keyframes added as global CSS or inside a <style> tag somewhere in your app:
const globalStyles = `
@keyframes shimmer {
  0% {
    background-position: -400% 0;
  }
  100% {
    background-position: 400% 0;
  }
}
`;

// Remember to inject this style somewhere globally, like in index.html or your root component
// Or use a CSS/SCSS file to define this animation

const FeaturedShimmer = ({ count = 4 }) => {
  return (
    <>
      <style>{globalStyles}</style>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {Array(count).fill(0).map((_, idx) => (
          <ShimmerCard key={idx} />
        ))}
      </div>
    </>
  );
};

export default FeaturedShimmer;
