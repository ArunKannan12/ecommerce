import React, { useEffect, useState } from "react";
import axiosInstance from "../../api/axiosinstance";
import { toast } from "react-toastify";
import Category from '../../components/visitor/Category.jsx';
import FeaturedShimmer from '../../shimmer/FeaturedShimmer.jsx';
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";


const Store = () => {
  const { categorySlug } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  // States for filters and ordering
  const [products, setProducts] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(true);

  // Extract filters & search from URL params
  const searchQuery = searchParams.get("search") || "";
  const featuredFilter = searchParams.get("featured") === "true";
  const availableFilter = searchParams.get("is_available") === "true";
  const ordering = searchParams.get("ordering") || "";

  const navigate = useNavigate();

  // Fetch products with current filters and ordering
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

  // Update filters in URL when changed
  const updateFilters = (newFilters) => {
    // Merge new filters with existing params
    const updated = {
      search: searchQuery || undefined,
      featured: featuredFilter ? "true" : undefined,
      is_available: availableFilter ? "true" : undefined,
      ordering: ordering || undefined,
      ...newFilters
    };

    // Remove keys with undefined or false to clean URL
    Object.keys(updated).forEach(key => {
      if (updated[key] === undefined || updated[key] === false) {
        delete updated[key];
      }
    });

    setSearchParams(updated);
  };

  // On filter/order/category/search change, refetch
  useEffect(() => {
    fetchProducts();
  }, [categorySlug, searchQuery, featuredFilter, availableFilter, ordering]);

  // When category changes, update URL and clear filters if needed
  const handleCategorySelect = (slug) => {
    if (slug) {
      navigate(`/store/${slug}`);
    } else {
      navigate('/store');
    }
  };

  return (
    <>
      {/* Animation keyframes */}
      <style>
        {`
          @keyframes fadeSlideUp {
            0% {
              opacity: 0;
              transform: translateY(20px);
            }
            100% {
              opacity: 1;
              transform: translateY(0);
            }
          }
        `}
      </style>

      <div className="max-w-screen-xl mx-auto px-6 sm:px-8 lg:px-12 py-8">
        <h2 className="text-4xl font-extrabold mb-8 border-b-2 border-indigo-500 pb-4 text-gray-900">
          Store
        </h2>

        <div className="flex flex-col md:flex-row gap-8">
          {/* Left Sidebar: Categories */}
          <aside className="w-full md:w-64 sticky top-24 self-start p-6 bg-white rounded-xl shadow-lg border border-gray-200">
            <Category
              selectedCategorySlug={categorySlug}
              onSelectCategory={handleCategorySelect}
            />
          </aside>

          {/* Right Content: Filters + Products */}
          <div className="flex-1 flex flex-col">
            {/* Filters */}
            <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6 mb-6 flex flex-wrap items-center gap-6 justify-end">
              {/* Featured Filter */}
              <label className="flex items-center cursor-pointer whitespace-nowrap">
                <input
                  type="checkbox"
                  checked={featuredFilter}
                  onChange={e => updateFilters({ featured: e.target.checked ? "true" : undefined })}
                  className="form-checkbox h-5 w-5 text-indigo-600"
                />
                <span className="ml-2 text-gray-700 font-semibold select-none">Featured Only</span>
              </label>

              {/* Available Filter */}
              <label className="flex items-center cursor-pointer whitespace-nowrap">
                <input
                  type="checkbox"
                  checked={availableFilter}
                  onChange={e => updateFilters({ is_available: e.target.checked ? "true" : undefined })}
                  className="form-checkbox h-5 w-5 text-indigo-600"
                />
                <span className="ml-2 text-gray-700 font-semibold select-none">Available Only</span>
              </label>

              {/* Sort By */}
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

            {/* Products grid */}
            <section>
              {loadingProducts ? (
  <FeaturedShimmer />
) : products.length > 0 ? (
  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">
    {products.map((product, i) => (
      <div
        key={product.id}
        style={{
          animation: "fadeSlideUp 0.5s ease forwards",
          animationDelay: `${i * 100}ms`,
          opacity: 0,
          transform: "translateY(20px)",
        }}
        className="max-w-sm bg-white rounded-2xl shadow-md overflow-hidden flex flex-col
                   transform transition-transform duration-300
                   hover:shadow-xl hover:scale-105 cursor-pointer"
      >
        <Link to={`/products/${product.slug}`} className="block group">
          <div className="h-40 overflow-hidden">
            <img
              src={
                product.images?.length > 0
                  ? product.images[0].url  // ✅ use .url instead of .image
                  : "/placeholder.png"     // ✅ fallback
              }
              alt={product.images?.[0]?.alt_text || product.name}
              className="w-full h-full object-cover transition-transform duration-300 hover:scale-110"
            />
          </div>

          <div className="p-5 flex flex-col flex-grow">
            <h3
              className="text-lg font-semibold text-gray-900 truncate"
              title={product.name}
            >
              {product.name}
            </h3>
            <p className="mt-2 text-indigo-600 text-xl">
              ₹{product.price}
            </p>
          </div>
        </Link>
      </div>
    ))}
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
