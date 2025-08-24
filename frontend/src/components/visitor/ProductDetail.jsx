import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import axiosInstance from '../../api/axiosinstance';
import { toast } from 'react-toastify';
import ProductDetailShimmer from '../../shimmer/ProductDetailShimmer';
import { useAddToCartMutation, useGetCartQuery } from '../../contexts/cartSlice';
import { useAuth } from '../../contexts/authContext';

const ProductDetail = () => {
  const { productSlug } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated } = useAuth();

  const [product, setProduct] = useState(null);
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [currentImg, setCurrentImg] = useState(0);
  const [relatedProducts, setRelatedProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  const [addToCartMutation, { isLoading }] = useAddToCartMutation();
  const { refetch: refetchCart } = useGetCartQuery(undefined, { skip: !isAuthenticated });

  // Fetch product & related products
  useEffect(() => {
    const fetchProduct = async () => {
      setLoading(true);
      try {
        const res = await axiosInstance.get(`products/${productSlug}/`);
        const data = res.data;
        setProduct(data);
        if (data.variants?.length > 0) setSelectedVariant(data.variants[0]);

        const relatedRes = await axiosInstance.get(`products/${productSlug}/related/`);
        setRelatedProducts(relatedRes.data.results || []);
      } catch (error) {
        console.error("Failed to load product", error);
        toast.error("Product not found");
        navigate("/store");
      } finally {
        setLoading(false);
      }
    };
    fetchProduct();
  }, [productSlug, navigate]);

  // Quantity helpers
  const productQuantity = (task) => {
    const stock = selectedVariant?.stock ?? product?.stock ?? 0;
    setQuantity(q => {
      if (task === 'add') return q < stock ? q + 1 : q;
      if (task === 'sub') return q > 1 ? q - 1 : 1;
      return q;
    });
  };

  // Guest cart helper (localStorage)
  const addToLocalCart = (variantId, quantity) => {
    const cart = JSON.parse(localStorage.getItem("cart")) || [];
    const index = cart.findIndex(item => item.product_variant_id === variantId);

    if (index > -1) cart[index].quantity += quantity;
    else cart.push({ product_variant_id: variantId, quantity, source: "add_to_cart" });

    localStorage.setItem("cart", JSON.stringify(cart));
    window.dispatchEvent(new Event("cartUpdated"));
    toast.success("Added to cart locally");
  };

  // Add to cart
  const addToCart = async (variantId) => {
    if (!variantId) return toast.error("No variant selected");

    if (!isAuthenticated) {
      addToLocalCart(variantId, quantity);
      return;
    }

    try {
      await addToCartMutation({ product_variant: variantId, quantity }).unwrap();
      toast.success("Added to cart");
      refetchCart();
    } catch (error) {
      const variantError = error?.data?.product_variant?.[0];
      toast.error(variantError || error?.data?.detail || "Failed to add to cart");
    }
  };

  // Buy now
  const handleBuyNow = () => {
    if (!selectedVariant) return toast.error("Select a variant first");

    const minimalPayload = [{
      product_variant_id: selectedVariant.id,
      quantity,
      source: "buy_now",
      timestamp: Date.now()
    }];

    sessionStorage.setItem("buyNowMinimal", JSON.stringify(minimalPayload));

    if (!isAuthenticated) {
      navigate("/login", { state: { from: "/checkout" } });
    } else {
      navigate("/checkout");
    }
  };

  if (loading || !product) return <ProductDetailShimmer />;

  const variantImageUrls =
    selectedVariant?.images?.length > 0
      ? selectedVariant.images.map(img => img?.url || img?.image || img?.image_url)
      : product?.images?.map(img => img?.url || img?.image || img?.image_url) || [];

  // 🟢 Price & discount logic
  const basePrice = Number(selectedVariant?.base_price || 0);
  const finalPrice = Number(selectedVariant?.final_price || basePrice);
  const discount =
    basePrice > 0 && finalPrice < basePrice
      ? Math.round(((basePrice - finalPrice) / basePrice) * 100)
      : 0;

  return (
    <div className="p-6">
      <div className="flex flex-col md:flex-row gap-6 max-w-5xl mx-auto">
        {/* Images */}
        <div className="flex-1">
          {variantImageUrls.length > 0 ? (
            <>
              <div className="w-full h-80 flex items-center justify-center bg-gray-100 rounded-xl shadow-md overflow-hidden">
                <img
                  src={variantImageUrls[currentImg] || "/placeholder.png"}
                  alt={selectedVariant?.variant_name || product?.name}
                  className="max-w-full max-h-full object-contain"
                />
              </div>
              <div className="flex gap-2 mt-2 overflow-x-auto">
                {variantImageUrls.map((imgUrl, idx) => (
                  <div
                    key={idx}
                    className={`w-16 h-16 flex items-center justify-center rounded-md border ${
                      idx === currentImg ? "border-blue-500" : "border-gray-300"
                    } bg-gray-100 cursor-pointer`}
                    onClick={() => setCurrentImg(idx)}
                  >
                    <img
                      src={imgUrl || "/placeholder.png"}
                      alt=""
                      className="max-w-full max-h-full object-contain"
                    />
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="w-full h-80 bg-gray-200 flex items-center justify-center text-gray-400 rounded-xl">
              No Image Available
            </div>
          )}
        </div>

        {/* Details */}
        <div className="flex-1 space-y-4">
          <h1 className="text-3xl font-bold">{product.name}</h1>
          <p className="text-sm text-gray-500">
            Category: <span className="font-medium">{product.category?.name}</span>
          </p>

          {/* 🟢 Show Price + Discount */}
          <div className="flex items-center gap-3">
            <p className="text-2xl font-bold text-green-700">₹{finalPrice}</p>
            {discount > 0 && (
              <>
                <p className="text-lg text-gray-500 line-through">₹{basePrice}</p>
                <span className="bg-red-100 text-red-600 text-sm font-semibold px-2 py-1 rounded-md">
                  {discount}% OFF
                </span>
              </>
            )}
          </div>

          <p className="text-gray-700">{product.description}</p>

          {/* Variant selector */}
          {(product.variants?.length > 1 ||
            (product.variants?.length === 1 && product.variants[0]?.variant_name?.toLowerCase() !== 'default')) && (
            <div>
              <label className="block font-semibold mb-2">Select Variant:</label>
              <select
                value={selectedVariant?.id || ''}
                onChange={(e) => {
                  const variant = product.variants.find(v => v.id === parseInt(e.target.value));
                  setSelectedVariant(variant);
                  setQuantity(1);
                  setCurrentImg(0);
                }}
                className="border rounded px-2 py-1 w-full"
              >
                {product.variants.map(v => (
                  <option key={v.id} value={v.id}>
                    {v.variant_name} (SKU: {v.sku}) - Stock: {v.stock}
                  </option>
                ))}
              </select>
            </div>
          )}

          <p className="text-sm text-gray-600">Stock: {selectedVariant?.stock ?? 'N/A'}</p>
          <p className="text-sm text-gray-600">SKU: {selectedVariant?.sku ?? 'N/A'}</p>

          {/* Quantity controls */}
          <div className="flex items-center space-x-4 mt-4">
            <button onClick={() => productQuantity('sub')} disabled={quantity <= 1} className="w-10 h-10 flex justify-center items-center rounded-md border border-gray-300 text-gray-700 hover:bg-gray-200 transition">-</button>
            <span className="min-w-[30px] text-center text-lg font-medium">{quantity}</span>
            <button onClick={() => productQuantity('add')} className="w-10 h-10 flex justify-center items-center rounded-md border border-gray-300 text-gray-700 hover:bg-gray-200 transition">+</button>
          </div>

          {/* Cart / Buy Now */}
          <div className="flex gap-4 mt-6">
            <button onClick={() => addToCart(selectedVariant?.id)} disabled={isLoading || !selectedVariant || selectedVariant.stock === 0} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed">
              {isLoading ? 'Adding...' : 'Add to Cart'}
            </button>
            <button onClick={handleBuyNow} disabled={!selectedVariant || selectedVariant.stock === 0} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition">
              Buy Now
            </button>
          </div>
        </div>
      </div>

      {/* Related Products */}
      {relatedProducts.length > 0 && (
  <div className="mt-12">
    <h2 className="text-2xl font-bold mb-6 text-gray-800">Related Products</h2>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
      {relatedProducts.map((rp) => {
        // take the lowest prices among variants
        const minBasePrice = rp.variants?.length
          ? Math.min(...rp.variants.map(v => parseFloat(v.base_price)))
          : null;

        const minOfferPrice = rp.variants?.length
          ? Math.min(...rp.variants.map(v => parseFloat(v.final_price)))
          : null;

        const discount =
          minBasePrice && minOfferPrice
            ? Math.round(((minBasePrice - minOfferPrice) / minBasePrice) * 100)
            : 0;

        return (
          <div
            key={rp.id}
            className="group relative bg-white border rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden cursor-pointer"
            onClick={() => navigate(`/products/${rp.slug}`)}
          >
            {/* Image */}
            <div className="w-full h-48 flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 overflow-hidden">
              {rp.image_url ? (
                <img
                  src={rp.image_url}
                  alt={rp.name}
                  className="max-w-full max-h-full object-contain transform group-hover:scale-105 transition-transform duration-300"
                />
              ) : (
                <div className="text-gray-400 text-center w-full">No Image</div>
              )}
            </div>

            {/* Details */}
            <div className="p-4">
              <h3 className="text-base font-semibold text-gray-800 group-hover:text-indigo-600 line-clamp-1">
                {rp.name}
              </h3>

              {minOfferPrice !== null && (
                <div className="mt-1 flex items-center gap-2">
                  <p className="text-lg font-bold text-green-700">₹{minOfferPrice}</p>
                  {minBasePrice && minBasePrice > minOfferPrice && (
                    <>
                      <p className="text-sm text-gray-500 line-through">₹{minBasePrice}</p>
                      <span className="text-sm font-medium text-red-600">
                        {discount}% OFF
                      </span>
                    </>
                  )}
                </div>
              )}
            </div>

            {/* Hover Badge */}
            <div className="absolute top-3 right-3">
              <span className="bg-indigo-100 text-indigo-700 text-xs font-semibold px-2 py-1 rounded-full opacity-0 group-hover:opacity-100 transition duration-300">
                View
              </span>
            </div>
          </div>
        );
      })}
    </div>
  </div>
)}


    </div>
  );
};

export default ProductDetail;
