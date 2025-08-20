import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import axiosInstance from '../../api/axiosinstance';
import { toast } from 'react-toastify';
import ProductDetailShimmer from '../../shimmer/ProductDetailShimmer';
import { useAddToCartMutation, useGetCartQuery } from '../../contexts/cartSlice';
import { syncGuestcart } from '../../utils/syncGuestCart';
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
    else cart.push({ product_variant_id: variantId, quantity,source:"add_to_cart" });

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
          <p className="text-xl font-semibold text-green-700">
            ₹{selectedVariant
              ? Number(selectedVariant?.additional_price || 0) + Number(product?.price || 0)
              : product?.price}
          </p>
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

          <p className="text-sm text-gray-600">Stock: {selectedVariant?.stock ?? product?.stock ?? 'N/A'}</p>
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
        <div className="mt-10">
          <h2 className="text-lg font-bold mb-4">Related Products</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {relatedProducts.map((rp) => (
              <div key={rp.id} className="border p-2 rounded-lg shadow hover:shadow-lg transition cursor-pointer" onClick={() => navigate(`/products/${rp.slug}`)}>
                <div className="w-full h-40 flex items-center justify-center bg-gray-100 overflow-hidden rounded">
                  {rp.images?.[0]?.url ? (
                    <img src={rp.images[0].url} alt={rp.name} className="max-w-full max-h-full object-contain" />
                  ) : (
                    <div className="text-gray-400 text-center w-full">No Image</div>
                  )}
                </div>
                <h3 className="mt-2 font-semibold">{rp.name}</h3>
                <p className="text-green-700">₹{rp.price}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductDetail;
