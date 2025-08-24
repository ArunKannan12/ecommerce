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

  return (
    <>
  {/* Full width banner */}
  <div className="w-full">
    <BannerSlider />
  </div>

  {/* Responsive main content */}
  <div className="max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
    <h1 className="text-2xl sm:text-4xl font-bold mb-4 sm:mb-6">
      Welcome to MyStore
    </h1>
    <p className="mb-6 sm:mb-10 text-gray-700 text-sm sm:text-base">
      Explore our categories and find your favorite products.
    </p>

    <section>
      <h2 className="text-xl sm:text-2xl font-semibold mb-4 sm:mb-6">
        Featured Products
      </h2>

      {error && (
        <p className="text-red-600 mb-4 font-semibold">{error}</p>
      )}

      {loading ? (
        <FeaturedShimmer />
      ) : featured.length === 0 ? (
        <p className="text-gray-600">No featured products</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {featured.map((prod) => {
  const variant = prod.variants?.[0];
  const finalPrice = parseFloat(variant?.final_price || "0");
  const basePrice = parseFloat(variant?.base_price || "0");
  const isDiscounted = basePrice > 0 && finalPrice < basePrice;
  const discountPercent = isDiscounted
    ? Math.round(((basePrice - finalPrice) / basePrice) * 100)
    : 0;

  const imageUrl =
    prod.image_url ||
    variant?.images?.[0]?.url ||
    "https://cdn.pixabay.com/photo/2023/01/28/19/01/bird-7751561_1280.jpg";

  return (
    <Link
      key={prod.id}
      to={`/products/${prod.slug}`}
      className="group block bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-xl transition duration-300 hover:scale-[1.02]"
    >
      {/* Image */}
      <div className="relative aspect-w-4 aspect-h-3">
        <img
          src={imageUrl}
          alt={prod.name}
          className="object-cover w-full h-full transition duration-300 group-hover:scale-105"
        />
        {prod.featured && (
          <span className="absolute top-2 left-2 bg-yellow-500 text-white text-xs font-semibold px-2 py-1 rounded">
            Featured
          </span>
        )}
      </div>

      {/* Info */}
      <div className="p-4 sm:p-5">
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-1 truncate">
          {prod.name}
        </h2>
        <p className="text-sm text-gray-600 mb-2 line-clamp-2">
          {prod.description}
        </p>

        {/* Pricing */}
        <div className="flex items-center gap-2">
          <span className="text-base sm:text-lg font-bold text-gray-800">
            ₹{finalPrice.toFixed(2)}
          </span>
          {isDiscounted && (
            <>
              <span className="text-sm line-through text-red-500">
                ₹{basePrice.toFixed(2)}
              </span>
              <span className="text-xs font-medium text-green-600 bg-green-100 px-2 py-1 rounded-full">
                {discountPercent}% OFF
              </span>
            </>
          )}
        </div>

        {/* Stock */}
        {variant?.stock < 5 && (
          <p className="mt-2 text-xs text-red-600 font-medium">
            Only {variant.stock} left in stock!
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
