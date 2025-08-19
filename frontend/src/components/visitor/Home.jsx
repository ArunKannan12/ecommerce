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
      <div className="p-4 sm:p-8 w-full">
        <h1 className="text-2xl sm:text-4xl font-bold mt-8 sm:mt-12 mb-4 sm:mb-6">
          Welcome to MyStore
        </h1>
        <p className="mb-6 sm:mb-10 text-gray-700 text-sm sm:text-base">
          Explore our categories and find your favorite products.
        </p>

        <section>
          <h2 className="text-xl sm:text-2xl font-semibold mb-3 sm:mb-4">
            Featured Products
          </h2>

          {error && (
            <p className="text-red-600 mb-4 font-semibold">{error}</p>
          )}

          {loading ? (
            <FeaturedShimmer />
          ) : featured.length === 0 ? (
            <p>No featured products</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
              {featured.map((prod) => (
                <Link
                  key={prod.id}
                  to={`/products/${prod.slug}`}
                  className="transform transition duration-300 hover:shadow-xl hover:scale-105 cursor-pointer rounded overflow-hidden"
                >
                  <div className="bg-white border border-gray-200">
                    <img
                      className="w-full h-48 object-cover"
                      src={
                        prod.images && prod.images.length > 0
                          ? prod.images[0].url
                          : "https://cdn.pixabay.com/photo/2023/01/28/19/01/bird-7751561_1280.jpg"
                      }
                      alt={prod.name}
                    />
                    <div className="px-4 sm:px-6 py-3 sm:py-4">
                      <h2 className="font-bold text-lg sm:text-xl mb-1 sm:mb-2">
                        {prod.name}
                      </h2>
                      <p className="text-gray-700 text-sm sm:text-base">
                        {prod.description?.slice(0, 80)}...
                      </p>
                    </div>
                    <div className="px-4 sm:px-6 pt-3 pb-2">
                      <span className="inline-block bg-gray-200 rounded-full px-2 sm:px-3 py-1 text-xs sm:text-sm font-semibold text-gray-700 mr-2">
                        ₹{prod.price}
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}

        </section>
      </div>
    </>
  );
};

export default Home;
