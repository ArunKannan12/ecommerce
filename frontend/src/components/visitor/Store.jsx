import React, { useEffect, useState } from "react";
import axiosInstance from "../../api/axiosinstance";
import { toast } from "react-toastify";
import Category from '../../components/visitor/Category.jsx';
import FeaturedShimmer from '../../shimmer/FeaturedShimmer.jsx';
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import CustomSortDropdown from "../helpers/CustomSortDropDown.jsx";

const Store = () => {
  const { categorySlug } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [showFilters, setShowFilters] = useState(false);
  
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
  {/* Custom animation keyframes */}
  <style>
    {`
      @keyframes fadeSlideUp {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
      }
    `}
  </style>

  <div className="px-4 sm:px-8 lg:px-12 py-6 sm:py-8">
    {/* Page Heading */}
    <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-gray-900 mb-8 border-b-2 border-[#155dfc] pb-4">
      Store
    </h2>

    <div className="flex flex-col md:flex-row gap-8">
      {/* Sidebar for Desktop */}
      <aside className="hidden md:block w-full md:w-64 md:sticky md:top-24 self-start p-4 sm:p-6 bg-white rounded-xl shadow-lg border border-gray-200 z-10">
        <Category
          selectedCategorySlug={categorySlug}
          onSelectCategory={handleCategorySelect}
        />
      </aside>

      {/* Mobile Category Dropdown */}
      <div className="md:hidden px-4 mb-4">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="w-full bg-[#155dfc] text-white rounded-lg py-2 font-semibold"
        >
          {showFilters ? "Hide Categories" : "Show Categories"}
        </button>

        {showFilters && (
          <div className="mt-2 bg-white rounded-xl shadow-md border border-gray-200 p-4">
            <Category
              selectedCategorySlug={categorySlug}
              onSelectCategory={handleCategorySelect}
            />
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Filters */}
        <div className="w-full bg-white rounded-xl shadow-md border border-gray-200 p-4 sm:p-6 mb-6 flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-4 sm:gap-6">
          <div className="flex flex-col sm:flex-row gap-4 sm:gap-6">
            {/* Featured Only */}
            <label className="flex items-center cursor-pointer select-none">
              <input
                type="checkbox"
                checked={featuredFilter}
                onChange={e =>
                  updateFilters({ featured: e.target.checked ? "true" : undefined })
                }
                className="form-checkbox h-5 w-5 text-indigo-600 rounded transition duration-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
              <span className="ml-2 text-gray-700 font-semibold hover:text-indigo-600 transition-colors">
                Featured Only
              </span>
            </label>

            {/* Available Only */}
            <label className="flex items-center cursor-pointer select-none">
              <input
                type="checkbox"
                checked={availableFilter}
                onChange={e =>
                  updateFilters({ is_available: e.target.checked ? "true" : undefined })
                }
                className="form-checkbox h-5 w-5 text-indigo-600 rounded transition duration-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
              <span className="ml-2 text-gray-700 font-semibold hover:text-indigo-600 transition-colors">
                Available Only
              </span>
            </label>
          </div>


          <div className="w-full sm:w-auto relative">
            <div className="relative">
              <CustomSortDropdown ordering={ordering} updateFilters={updateFilters} />
            </div>
          </div>

        </div>

        {/* Products */}
        <section>
          {loadingProducts ? (
            <FeaturedShimmer />
          ) : products.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
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
                  variant?.images?.[0]?.url

                return (
                  <div
                    key={product.id}
                    className="bg-white rounded-2xl shadow-md
                     overflow-hidden flex flex-col transition-all
                      duration-300 hover:shadow-indigo-200 
                    hover:scale-[1.03] cursor-pointer 
                    z-0 animate-[fadeSlideUp_0.5s_ease_forwards] opacity-0"
                    style={{ animationDelay: `${i * 100}ms` }}
                  >
                    <Link to={`/products/${product.slug}`} className="block group">
                      <div className="relative aspect-[4/3] overflow-hidden z-0">
                        <img
                          src={imageUrl}
                          alt={variant?.images?.[0]?.alt_text || product.name}
                          loading="lazy"
                           className="w-full h-full object-cover transition-transform
                            duration-300 sm:group-hover:scale-110"
                        />
                        {product.featured && (
                          <span className="absolute top-2 left-2 bg-yellow-500 text-white text-[10px] font-bold
                           uppercase tracking-wide px-2 py-1 rounded shadow">
                            Featured
                          </span>
                        )}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent 
                        opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                      </div>

                      <div className="p-4 sm:p-5 flex flex-col flex-grow">
                        <h3  className="text-base sm:text-lg font-semibold tracking-tight text-gray-900 truncate" title={product.name}>
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
                            <span className="text-xs font-semibold text-green-700 bg-green-100 px-2 py-1 rounded-full shadow-sm">
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
            <div className="text-center text-gray-500 mt-20">
              <p className="text-xl font-medium">No products available</p>
            </div>
          )}
        </section>
      </div>
    </div>
  </div>
</>
  );
};

export default Store;