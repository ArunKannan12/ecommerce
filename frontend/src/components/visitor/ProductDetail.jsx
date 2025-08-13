import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import axiosInstance from '../../api/axiosinstance';
import { toast } from 'react-toastify';
import ProductDetailShimmer from '../../shimmer/ProductDetailShimmer';
import { useAddToCartMutation } from '../../contexts/cartSlice';

const ProductDetail = () => {
    const {productSlug} = useParams();
    const [product,setProduct] = useState(null)
    const [loading,setLoading] = useState(false)
    const navigate = useNavigate();
    const [quantity,setQuantity] = useState(1)
    const [relatedProducts,setRelatedProducts] = useState([])
    const [selectedVariant,setSelectedVariant] = useState(null)

    const [addToCartMutation, { isLoading }] = useAddToCartMutation();

    
    useEffect(()=>{
      const fetchProduct = async()=>{
        setLoading(true)
        try {
          const res = await axiosInstance.get(`products/${productSlug}/`);
          const data = res.data
          setProduct(data)
          if (data.variants?.length) {
            setSelectedVariant(data.variants[0]);
            setQuantity(1)
          }

          const relatedRes = await axiosInstance.get(`products/${productSlug}/related/`);
          const relatedData = relatedRes.data.results
          setRelatedProducts(relatedData);
          } catch (error) {
            console.error("failed to load produt",error);
            toast.error("Product not found")
            navigate("/store")
          }finally{
            setLoading(false)
          }
        }
        fetchProduct()
    },[productSlug,navigate])

    const productQuantity = (task) => {
        // If no variants at all, allow quantity change without variant check
        if (product?.variants?.length === 0) {
          setQuantity(q => {
            if (task === 'add') {
              return q + 1;  // no stock limit in this simple case, or you can add product-level stock if available
            } else if (task === 'sub') {
              return q > 1 ? q - 1 : 1;
            }
            return q;
          });
          return;
        }

        // If variants exist, variant must be selected
        if (!selectedVariant) {
          toast.error("No variant selected");
          return;
        }

        const stock = selectedVariant.stock;

        if (task === 'add') {
          setQuantity(q => {
            if (q >= stock) {
              toast.error("Reached maximum stock");
              return q;
            }
            return q + 1;
          });
        } else if (task === 'sub') {
          setQuantity(q => (q > 1 ? q - 1 : 1));
        }
};

const addToLocalCart = (productVariantId, productId, quantity) => {
  let cart = JSON.parse(localStorage.getItem("cart")) || [];

  // Key: variant if exists else product
  const key = productVariantId ?? productId;

  const existingIndex = cart.findIndex(item => item.key === key);

  if (existingIndex > -1) {
    cart[existingIndex].quantity += quantity;
  } else {
    cart.push({ key, product_variant_id: productVariantId, product_id: productId, quantity });
  }

  localStorage.setItem("cart", JSON.stringify(cart));
};

const addToCart = async (productVariantId) => {
    const isAuthenticated = Boolean(localStorage.getItem("access_token")); // check auth

    if (!isAuthenticated) {
      // Guest: update localStorage + dispatch event
      let cart = JSON.parse(localStorage.getItem("cart")) || [];
      const key = productVariantId ?? product?.id;
      const existingIndex = cart.findIndex((item) => item.key === key);

      if (existingIndex > -1) {
        cart[existingIndex].quantity += quantity;
      } else {
        cart.push({
          key,
          product_variant_id: productVariantId,
          product_id: product?.id,
          quantity,
        });
      }

      localStorage.setItem("cart", JSON.stringify(cart));
      window.dispatchEvent(new Event("cartUpdated")); // Notify Navbar
      toast.success("Added to cart locally.");
      return;
    }

    // Authenticated: send to backend
    try {
      const payload =
        product?.variants?.length > 0
          ? { product_variant_id: productVariantId, quantity }
          : { product_id: product?.id, quantity };

      await addToCartMutation(payload).unwrap(); // mutation from RTK
      toast.success("Added to cart");

      // Refetch cart to update Navbar immediately
      refetchCart?.(); 
    } catch (error) {
      console.error(error);
      toast.error("Failed to add to cart");
    }
  };
  



  return (
   <div className="p-6">
      {loading || !product ? (
        <ProductDetailShimmer />
      ) : (
        <div className="p-4 max-w-5xl mx-auto">
          <div className="flex flex-col md:flex-row gap-6">
            <div className="flex-1">
              {selectedVariant && selectedVariant.images?.length > 0 ? (
                <img
                  src={`http://localhost:8000${selectedVariant.images[0].image}`}
                  alt={selectedVariant.images[0].alt_text || selectedVariant.variant_name}
                  className="w-full h-80 object-cover rounded-xl shadow-md"
                />
              ) : product.images?.length > 0 ? (
                <img
                  src={`http://localhost:8000${product.images[0].image}`}
                  alt={product.images[0].alt_text || product.name}
                  className="w-full h-80 object-cover rounded-xl shadow-md"
                />
              ) : (
                <div className="w-full h-80 bg-gray-200 rounded-xl flex items-center justify-center text-gray-400">
                  No Image Available
                </div>
              )}
            </div>

            <div className="flex-1 space-y-4">
              <h1 className="text-3xl font-bold">{product.name}</h1>
              <p className="text-sm text-gray-500">
                Category: <span className="font-medium">{product.category?.name}</span>
              </p>
              <p className="text-xl font-semibold text-green-700">
                ₹
                {selectedVariant
                  ? Number(selectedVariant.additional_price) + Number(product.price)
                  : product.price}
              </p>
              <p className="text-gray-700">{product.description}</p>

              {/* Variant selector */}
              {product.variants?.length > 0 && (
                <div>
                  <label className="block font-semibold mb-2">Select Variant:</label>
                  <select
                    value={selectedVariant?.id || ''}
                    onChange={(e) => {
                      const variant = product.variants.find(
                        (v) => v.id === parseInt(e.target.value),
                      );
                      setSelectedVariant(variant);
                      setQuantity(1);
                    }}
                    className="border rounded px-2 py-1 w-full"
                  >
                    {product.variants.map((variant) => (
                      <option key={variant.id} value={variant.id}>
                        {variant.variant_name} (SKU: {variant.sku}) - Stock: {variant.stock}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Show stock and SKU for selected variant */}
              <p className="text-sm text-gray-600">Stock: {selectedVariant?.stock ?? 'N/A'}</p>
              <p className="text-sm text-gray-600">SKU: {selectedVariant?.sku ?? 'N/A'}</p>

              {/* Quantity controls */}
              <div className="flex items-center space-x-4 mt-4">
                <button
                  onClick={() => productQuantity('sub')}
                  disabled={quantity <= 1}
                  className="w-10 h-10 flex justify-center items-center rounded-md border border-gray-300 text-gray-700 hover:bg-gray-200 transition"
                >
                  -
                </button>
                <span className="min-w-[30px] text-center text-lg font-medium">{quantity}</span>
                <button
                  onClick={() => productQuantity('add')}
                  className="w-10 h-10 flex justify-center items-center rounded-md border border-gray-300 text-gray-700 hover:bg-gray-200 transition"
                >
                  +
                </button>
              </div>

              {/* Add to Cart / Buy Now */}
              <div className="flex gap-4 mt-6">
                <button
                  onClick={() => addToCart(selectedVariant?.id)}
                  disabled={
                    isLoading ||
                    (product?.variants?.length > 0 &&
                      (!selectedVariant || selectedVariant.stock === 0)) ||
                    (product?.variants?.length === 0 && (!product.stock || product.stock <= 0))
                  }
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Adding...' : 'Add to Cart'}
                </button>
                <button
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
                  // You can add buy now logic here later
                >
                  Buy Now
                </button>
              </div>
            </div>
          </div>

          {/* Related products */}
          <div className="mt-10">
            <h2 className="text-lg font-bold mb-4">Related Products</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {relatedProducts.map((rp) => (
                <div
                  key={rp.id}
                  className="border p-2 rounded-lg shadow hover:shadow-lg transition cursor-pointer"
                  onClick={() => navigate(`/products/${rp.slug}`)}
                >
                  {rp.images?.length > 0 && (
                    <img
                      src={`http://localhost:8000${rp.images[0].image}`}
                      alt={rp.name}
                      className="w-full h-40 object-cover rounded"
                    />
                  )}
                  <h3 className="mt-2 font-semibold">{rp.name}</h3>
                  <p className="text-green-700">₹{rp.price}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductDetail;
