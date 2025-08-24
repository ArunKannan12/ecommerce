import React, { useEffect, useState } from "react";
import axiosInstance from "../../api/axiosinstance";
import { toast } from "react-toastify";
import Category from '../../components/visitor/Category.jsx';
import FeaturedShimmer from '../../shimmer/FeaturedShimmer.jsx';
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";

const Store = () => {
  const { categorySlug } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const [products, setProducts] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(true);

  const searchQuery = searchParams.get("search") || "";
  const featuredFilter = searchParams.get("featured") === "true";
  const availableFilter = searchParams.get("is_available") === "true";
  const ordering = searchParams.get("ordering") || "";

  const navigate = useNavigate();

  const fetchProducts = async () => {
    setLoadingProducts(true);
    try {
      const params = {
        search: searchQuery || undefined,
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
      search: searchQuery || undefined,
      featured: featuredFilter ? "true" : undefined,
      is_available: availableFilter ? "true" : undefined,
      ordering: ordering || undefined,
      ...newFilters
    };

    Object.keys(updated).forEach(key => {
      if (updated[key] === undefined || updated[key] === false) {
        delete updated[key];
      }
    });

    setSearchParams(updated);
  };

  useEffect(() => {
    fetchProducts();
  }, [categorySlug, searchQuery, featuredFilter, availableFilter, ordering]);

  const handleCategorySelect = (slug) => {
    navigate(slug ? `/store/${slug}` : '/store');
  };

  return (
    <>
      <style>
        {`
          @keyframes fadeSlideUp {
            0% { opacity: 0; transform: translateY(20px); }
            100% { opacity: 1; transform: translateY(0); }
          }
        `}
      </style>

      <div className="max-w-screen-xl mx-auto px-6 sm:px-8 lg:px-12 py-8">
        <h2 className="text-4xl font-extrabold mb-8 border-b-2 border-indigo-500 pb-4 text-gray-900">
          Store
        </h2>

        <div className="flex flex-col md:flex-row gap-8">
          {/* Sidebar */}
          <aside className="w-full md:w-64 sticky top-24 self-start p-6 bg-white rounded-xl shadow-lg border border-gray-200">
            <Category
              selectedCategorySlug={categorySlug}
              onSelectCategory={handleCategorySelect}
            />
          </aside>

          {/* Main Content */}
          <div className="flex-1 flex flex-col">
            {/* Filters */}
            <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6 mb-6 flex flex-wrap items-center gap-6 justify-end">
              <label className="flex items-center cursor-pointer whitespace-nowrap">
                <input
                  type="checkbox"
                  checked={featuredFilter}
                  onChange={e => updateFilters({ featured: e.target.checked ? "true" : undefined })}
                  className="form-checkbox h-5 w-5 text-indigo-600"
                />
                <span className="ml-2 text-gray-700 font-semibold select-none">Featured Only</span>
              </label>

              <label className="flex items-center cursor-pointer whitespace-nowrap">
                <input
                  type="checkbox"
                  checked={availableFilter}
                  onChange={e => updateFilters({ is_available: e.target.checked ? "true" : undefined })}
                  className="form-checkbox h-5 w-5 text-indigo-600"
                />
                <span className="ml-2 text-gray-700 font-semibold select-none">Available Only</span>
              </label>

              <div className="ml-auto min-w-[180px]">
                <label htmlFor="ordering" className="block font-semibold mb-1 text-gray-700">
                  Sort By
                </label>
                <select
                  id="ordering"
                  value={ordering}
                  onChange={e => updateFilters({ ordering: e.target.value || undefined })}
                  className="w-full border border-gray-300 rounded-md p-2 text-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Default</option>
                  <option value="price">Price: Low to High</option>
                  <option value="-price">Price: High to Low</option>
                  <option value="created_at">Newest First</option>
                  <option value="-created_at">Oldest First</option>
                  <option value="name">Name: A-Z</option>
                  <option value="-name">Name: Z-A</option>
                </select>
              </div>
            </div>

            {/* Products */}
            <section>
              {loadingProducts ? (
                <FeaturedShimmer />
              ) : products.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">
                  {products.map((product, i) => {
                    const variant = product.variants?.[0];
                    const finalPrice = parseFloat(variant?.final_price || "0");
                    const basePrice = parseFloat(variant?.base_price || "0");
                    const isDiscounted = basePrice > 0 && finalPrice < basePrice;
                    const discountPercent = isDiscounted
                      ? Math.round(((basePrice - finalPrice) / basePrice) * 100)
                      : 0;

                    const imageUrl =
                      product.image_url ||
                      variant?.images?.[0]?.url ||
                      "https://cdn.pixabay.com/photo/2023/01/28/19/01/bird-7751561_1280.jpg";

                    return (
                      <div
                        key={product.id}
                        style={{
                          animation: "fadeSlideUp 0.5s ease forwards",
                          animationDelay: `${i * 100}ms`,
                          opacity: 0,
                          transform: "translateY(20px)",
                        }}
                        className="bg-white rounded-2xl shadow-md overflow-hidden flex flex-col transition-transform duration-300 hover:shadow-xl hover:scale-105 cursor-pointer"
                      >
                        <Link to={`/products/${product.slug}`} className="block group">
                          <div className="h-48 overflow-hidden relative">
                            <img
                              src={imageUrl}
                              alt={variant?.images?.[0]?.alt_text || product.name}
                              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                            />
                            {product.featured && (
                              <span className="absolute top-2 left-2 bg-yellow-500 text-white text-xs font-semibold px-2 py-1 rounded">
                                Featured
                              </span>
                            )}
                          </div>

                          <div className="p-5 flex flex-col flex-grow">
                            <h3 className="text-lg font-semibold text-gray-900 truncate" title={product.name}>
                              {product.name}
                            </h3>

                            <div className="mt-2 flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="text-xl font-bold text-gray-900">
                                  ₹{finalPrice.toFixed(2)}
                                </span>
                                {isDiscounted && (
                                  <span className="text-sm text-red-500 line-through">
                                    ₹{basePrice.toFixed(2)}
                                  </span>
                                )}
                              </div>

                              {isDiscounted && (
                                <span className="text-xs font-semibold text-green-700 bg-green-100 px-2 py-1 rounded-full">
                                  {discountPercent}% OFF
                                </span>
                              )}
                            </div>

                            {variant?.stock === 0 && (
                              <p className="mt-2 text-xs text-gray-500 font-medium">Out of stock</p>
                            )}
                            {variant?.stock > 0 && variant?.stock < 5 && (
                              <p className="mt-2 text-xs text-red-600 font-medium">
                                Only {variant.stock} left in stock!
                              </p>
                            )}
                          </div>
                        </Link>
                      </div>
                    );
                  })}
                </div>
              ) : (
                  <p className="text-center text-gray-500 text-xl mt-20">
                  No products available.
                </p>
              )}
            </section>
          </div>
        </div>
      </div>
    </>
  );
};

export default Store;