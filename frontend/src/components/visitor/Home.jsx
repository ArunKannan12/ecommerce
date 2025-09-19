import React, { useEffect, useState } from "react";
import BannerSlider from "./BannerSlide";
import axiosInstance from "../../api/axiosinstance";
import FeaturedShimmer from "../../shimmer/FeaturedShimmer.jsx";
import { Link } from "react-router-dom";

const Home = () => {
  const [featured, setFeatured] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchFeaturedProducts = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axiosInstance.get("products/featured/");
      const data = res.data.results;
      setFeatured(data);
    } catch (err) {
      setError(err.message || "Failed to load featured products");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFeaturedProducts();
  }, []);
  console.log(featured,'featured');
  
  return (
   <>
  {/* Full width banner */}
  <div className="w-full">
    <BannerSlider />
  </div>

  {/* Responsive main content */}
  <div className="w-full px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
    <h1 className="text-2xl sm:text-4xl font-bold mb-4 sm:mb-6">
      Welcome to Beston!
    </h1>
    <p className="mb-6 sm:mb-10 text-gray-700 text-sm sm:text-base">
      Explore our categories and find your favorite products.
    </p>

    <section>
  <h2 className="text-xl sm:text-2xl font-semibold mb-4 sm:mb-6">
    Featured Products
  </h2>

  {error && <p className="text-red-600 mb-4 font-semibold">{error}</p>}

  {loading ? (
  <FeaturedShimmer />
) : featured.length === 0 ? (
  <p className="text-gray-600">No featured products</p>
) : (
  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4 sm:gap-6">
    {featured.map((prod) => {
      const activeVariants = prod.variants?.filter(v => v.is_active) || [];

      const cheapestVariant = activeVariants.reduce((lowest, current) => {
        const currentPrice = parseFloat(current.final_price || current.offer_price || current.base_price || "0");
        const lowestPrice = parseFloat(lowest.final_price || lowest.offer_price || lowest.base_price || "0");
        return currentPrice < lowestPrice ? current : lowest;
      }, activeVariants[0]);

      const finalPrice = parseFloat(cheapestVariant?.final_price || "0");
      const basePrice = parseFloat(cheapestVariant?.base_price || "0");
      const isDiscounted = basePrice > 0 && finalPrice < basePrice;
      const discountPercent = isDiscounted
        ? Math.round(((basePrice - finalPrice) / basePrice) * 100)
        : 0;

      const imageUrl =
        cheapestVariant?.primary_image_url ||
        cheapestVariant?.images?.[0]?.url ||
        prod.image_url ||
        prod.category?.image_url ||
        "/placeholder.png";

      return (
        <Link
          key={prod.id}
          to={`/products/${prod.slug}`}
          className="group block bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition duration-300"
        >
          {/* Image */}
          <div className="relative w-full aspect-[4/3]">
            <img
              src={imageUrl}
              alt={prod.name}
              loading="lazy"
              className="object-cover w-full h-full transition duration-300 group-hover:scale-105"
            />
            {prod.featured && (
              <span className="absolute top-2 left-2 bg-yellow-500 text-white text-xs font-semibold px-2 py-1 rounded">
                Featured
              </span>
            )}
          </div>

          {/* Info */}
          <div className="p-2 sm:p-3">
            <h2 className="text-sm sm:text-base font-semibold text-gray-900 mb-1 truncate">
              {prod.name}
            </h2>
            <p className="text-xs text-gray-600 mb-1 line-clamp-2">
              {prod.description}
            </p>

            {/* Pricing */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm sm:text-base font-bold text-gray-800">
                From ₹{finalPrice.toFixed(2)}
              </span>
              {isDiscounted && (
                <>
                  <span className="text-xs line-through text-red-500">
                    ₹{basePrice.toFixed(2)}
                  </span>
                  <span className="text-[10px] sm:text-xs font-medium text-green-600 bg-green-100 px-1 py-0.5 rounded-full">
                    {discountPercent}% OFF
                  </span>
                </>
              )}
              {activeVariants.length > 1 && (
                <span className="text-[10px] sm:text-xs font-medium text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full">
                  {activeVariants.length} options
                </span>
              )}
            </div>

            {/* Stock */}
            {cheapestVariant?.stock > 0 && cheapestVariant?.stock < 5 && (
              <p className="mt-1 text-[10px] sm:text-xs text-red-600 font-medium">
                Only {cheapestVariant.stock} left!
              </p>
            )}
          </div>
        </Link>
      );
    })}
  </div>
)}
</section>
  </div>
</>


  );
};

export default Home;
