import React, { useEffect, useState } from "react";
import axiosInstance from "../../api/axiosinstance";
import { toast } from "react-toastify";
import Category from "../../components/visitor/Category.jsx";
import FeaturedShimmer from "../../shimmer/FeaturedShimmer.jsx";
import { Link, useNavigate, useParams } from "react-router-dom";
import CustomSortDropdown from "../helpers/CustomSortDropDown.jsx";
import { motion } from "framer-motion";

const Store = () => {
  const { categorySlug } = useParams();
  const [showFilters, setShowFilters] = useState(false);

  const [products, setProducts] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(true);

  const featuredFilter = false; // default, controlled via button
  const availableFilter = false; // default, controlled via button
  const ordering = ""; // default ordering

  const navigate = useNavigate();

  const fetchProducts = async () => {
    setLoadingProducts(true);
    try {
      const params = {
        category_slug: categorySlug || undefined,
        featured: featuredFilter ? true : undefined,
        is_available: availableFilter ? true : undefined,
        ordering: ordering || undefined,
      };
      const res = await axiosInstance.get("products/", { params });
      setProducts(res.data.results || res.data);
    } catch (error) {
      console.error("Error fetching products:", error);
      toast.error("Failed to load products!");
    } finally {
      setLoadingProducts(false);
    }
  };

  const updateFilters = (newFilters) => {
    const updated = {
      featured: featuredFilter ? "true" : undefined,
      is_available: availableFilter ? "true" : undefined,
      ordering: ordering || undefined,
      ...newFilters,
    };
    Object.keys(updated).forEach((key) => {
      if (updated[key] === undefined || updated[key] === false) delete updated[key];
    });
    navigate({
      pathname: categorySlug ? `/store/${categorySlug}` : "/store",
      search: new URLSearchParams(updated).toString(),
    });
  };

  useEffect(() => {
    fetchProducts();
  }, [categorySlug, featuredFilter, availableFilter, ordering]);

  const handleCategorySelect = (slug) => {
    navigate(slug ? `/store/${slug}` : "/store");
  };

  return (
    <div className="px-4 sm:px-8 lg:px-12 py-6 sm:py-10">
      {/* Hero Section */}
      <div className="text-center mb-10 relative">
        <h1 className="text-4xl sm:text-5xl font-extrabold mb-4 text-gray-900">
          Discover Our Collection
        </h1>
        <p className="text-lg text-gray-600 mb-6">
          Handpicked products just for you
        </p>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Sidebar */}
        <aside className="hidden md:block w-full md:w-64 sticky top-24 self-start p-5 bg-white rounded-3xl shadow-xl border border-gray-100 overflow-y-auto max-h-[80vh]">
          <Category
            selectedCategorySlug={categorySlug}
            onSelectCategory={handleCategorySelect}
          />
        </aside>

        {/* Mobile Filters */}
        <div className="md:hidden mb-4">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="w-full bg-indigo-600 text-white rounded-2xl py-2 font-semibold shadow-md"
          >
            {showFilters ? "Hide Categories" : "Show Categories"}
          </button>
          {showFilters && (
            <div className="mt-3 bg-white rounded-2xl shadow-md p-5 border border-gray-200">
              <Category
                selectedCategorySlug={categorySlug}
                onSelectCategory={handleCategorySelect}
              />
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Filter Bar */}
          <div className="w-full bg-white rounded-3xl shadow-md border border-gray-100 p-5 mb-6 flex flex-wrap items-center gap-4 justify-between">
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() =>
                  updateFilters({ featured: featuredFilter ? undefined : "true" })
                }
                className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                  featuredFilter
                    ? "bg-indigo-600 text-white shadow-md"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                Featured
              </button>

              <button
                onClick={() =>
                  updateFilters({ is_available: availableFilter ? undefined : "true" })
                }
                className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                  availableFilter
                    ? "bg-green-600 text-white shadow-md"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                In Stock
              </button>
            </div>

            <div>
              <CustomSortDropdown ordering={ordering} updateFilters={updateFilters} />
            </div>
          </div>

          {/* Product Grid */}
          <section>
            {loadingProducts ? (
              <FeaturedShimmer />
            ) : products.length > 0 ? (
              <motion.div layout className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {products.map((product, i) => {
                  const imageUrl = product.image_url || product.category?.image_url;
                  const prices = product.variants.map((v) =>
                    parseFloat(v.final_price || v.offer_price || v.base_price || "0")
                  );
                  const lowestPrice = prices.length > 0 ? Math.min(...prices) : null;
                  const isNew =
                    new Date(product.created_at) >=
                    new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

                  return (
                    <motion.div
                      key={product.id}
                      initial={{ opacity: 0, y: 30 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="bg-white rounded-3xl shadow-lg overflow-hidden flex flex-col hover:shadow-2xl transition-all duration-300 group"
                    >
                      <Link to={`/products/${product.slug}`} className="block group">
                        <div className="relative aspect-[4/3] overflow-hidden">
                          <img
                            src={imageUrl}
                            alt={product.name}
                            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                          />
                          {product.featured && (
                            <span className="absolute top-2 left-2 bg-yellow-500 text-white text-xs font-bold px-2 py-1 rounded-full shadow">
                              Featured
                            </span>
                          )}
                          {isNew && (
                            <span className="absolute top-2 right-2 bg-pink-600 text-white text-xs font-bold px-2 py-1 rounded-full shadow">
                              New
                            </span>
                          )}
                        </div>

                        <div className="p-5 flex flex-col flex-grow">
                          <h3
                            className="text-base font-semibold text-gray-900 truncate capitalize group-hover:text-indigo-600 transition"
                            title={product.name}
                          >
                            {product.name}
                          </h3>

                          {lowestPrice !== null && (
                            <div className="mt-3 flex items-center justify-between">
                              <span className="text-lg font-bold text-gray-900">
                                From ₹{lowestPrice.toFixed(2)}
                              </span>
                              {product.variants.length > 1 && (
                                <span className="text-xs font-medium text-gray-600 bg-gray-100 px-2 py-1 rounded-full">
                                  {product.variants.length} options
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </Link>
                    </motion.div>
                  );
                })}
              </motion.div>
            ) : (
              <div className="text-center text-gray-500 mt-20">
                <p className="text-xl font-medium">No products available</p>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
};

export default Store;
