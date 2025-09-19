// components/admin/modals/AddProductModal.jsx
import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axiosInstance from "../../../api/axiosinstance";
import { toast } from "react-toastify";

const AddProductModal = ({ onClose, onSuccess, product = null }) => {
  const isEdit = !!product;

  // 🔹 Product states
  const [name, setName] = useState(product?.name || "");
  const [slug, setSlug] = useState(product?.slug || "");
  const [slugEdited, setSlugEdited] = useState(false);
  const [description, setDescription] = useState(product?.description || "");
  const [category, setCategory] = useState(product?.category?.id || "");
  const [categories, setCategories] = useState([]);
  const [isAvailable, setIsAvailable] = useState(product?.is_available ?? true);
  const [featured, setFeatured] = useState(product?.featured ?? false);
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(product?.image_url || null);
  const [loading, setLoading] = useState(false);

  // 🔹 Variants state
  const [variants, setVariants] = useState(
    product?.variants?.length
      ? product.variants.map((v) => ({
          id: v.id,
          variant_name: v.variant_name,
          sku: v.sku || "",
          base_price: v.base_price,
          offer_price: v.offer_price || "",
          stock: v.stock,
          is_active: v.is_active,
          allow_return: v.allow_return,
          return_days: v.return_days || 0,
          allow_replacement: v.allow_replacement,
          replacement_days: v.replacement_days || 0,
          images: [],
          existingImages: v.images || [],
        }))
      : [
          {
            variant_name: "",
            sku: "",
            base_price: "",
            offer_price: "",
            stock: "",
            is_active: true,
            allow_return: false,
            return_days: 0,
            allow_replacement: false,
            replacement_days: 0,
            images: [],
            existingImages: [],
          },
        ]
  );

  // Auto-generate slug
  useEffect(() => {
    if (!slugEdited && name) {
      const generatedSlug = name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "");
      setSlug(generatedSlug);
    } else if (!name) {
      setSlug("");
      setSlugEdited(false);
    }
  }, [name, slugEdited]);

  // Fetch categories
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const res = await axiosInstance.get("/categories/");
        const sorted = res.data.results.sort((a, b) =>
          a.name.localeCompare(b.name)
        );
        setCategories(sorted);
      } catch (err) {
        const errMsg = err?.response?.data?.detail;
        toast.error(errMsg || "Failed to fetch categories");
      }
    };
    fetchCategories();
  }, []);

  // Preview product image
  useEffect(() => {
    if (!image) return;
    const objectUrl = URL.createObjectURL(image);
    setPreview(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [image]);

  // Variant handlers
  const handleVariantChange = (index, field, value) => {
    const updated = [...variants];
    updated[index][field] = value;
    setVariants(updated);
  };

  const handleVariantImages = (index, files) => {
    const updated = [...variants];
    updated[index].images = Array.from(files);
    setVariants(updated);
  };

  const addVariant = () => {
    setVariants([
      ...variants,
      {
        variant_name: "",
        sku: "",
        base_price: "",
        offer_price: "",
        stock: "",
        is_active: true,
        allow_return: false,
        return_days: 0,
        allow_replacement: false,
        replacement_days: 0,
        images: [],
        existingImages: [],
      },
    ]);
  };

  const removeVariant = (index) => {
    if (variants.length === 1) {
      toast.error("At least one variant is required");
      return;
    }
    setVariants(variants.filter((_, i) => i !== index));
  };

  // Handle submit
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !slug || !category) {
      toast.error("Please fill all required fields");
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();

      // Product fields
      formData.append("name", name);
      formData.append("slug", slug);
      formData.append("description", description);
      formData.append("category", category);
      formData.append("is_available", isAvailable);
      formData.append("featured", featured);
      if (image) formData.append("image", image);

      // Variants payload
      const variantsPayload = variants.map((variant, vIndex) => ({
        id: variant.id || null,
        variant_name: variant.variant_name,
        sku: variant.sku || "",
        base_price: variant.base_price,
        offer_price: variant.offer_price,
        stock: variant.stock,
        is_active: variant.is_active,
        allow_return: variant.allow_return,
        return_days: variant.return_days,
        allow_replacement: variant.allow_replacement,
        replacement_days: variant.replacement_days,
        images: variant.images.map((_, i) => ({
          image: `file-${vIndex}-${i}`,
        })),
      }));

      formData.append("variants", JSON.stringify(variantsPayload));

      // Attach files
      variants.forEach((variant, vIndex) => {
        variant.images.forEach((file, i) => {
          formData.append(`file-${vIndex}-${i}`, file);
        });
      });

      if (isEdit) {
        await axiosInstance.put(`/admin/products/${product.id}/`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        toast.success("Product updated successfully");
      } else {
        await axiosInstance.post("/admin/products/", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        toast.success("Product with variants added successfully");
      }

      onSuccess();
      onClose();
    } catch (err) {
      const errMsg =
        err?.response?.data?.name ||
        err?.response?.data?.slug ||
        err?.response?.data?.detail ||
        "Failed to save product";
      console.log(errMsg);
      
      toast.error(errMsg);
    }
    setLoading(false);
  };

  return (
    <AnimatePresence>
  <motion.div
    className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
  >
    <motion.div
      initial={{ scale: 0.9, opacity: 0, y: -50 }}
      animate={{ scale: 1, opacity: 1, y: 0 }}
      exit={{ scale: 0.9, opacity: 0, y: -50 }}
      transition={{ type: "spring", stiffness: 120, damping: 15 }}
      className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl p-6 overflow-y-auto max-h-[90vh]"
    >
      <h3 className="text-2xl font-bold mb-6 text-center text-gray-800">
        {isEdit ? "✏️ Edit Product" : "➕ Add Product"}
      </h3>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Product fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Product Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full p-3 border rounded-lg shadow-sm focus:ring-2 focus:ring-blue-400 outline-none transition"
          />
          <input
            type="text"
            placeholder="Slug"
            value={slug}
            onChange={(e) => {
              setSlug(e.target.value);
              setSlugEdited(true);
            }}
            required
            className="w-full p-3 border rounded-lg shadow-sm focus:ring-2 focus:ring-blue-400 outline-none transition"
          />
          <textarea
            placeholder="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full p-3 border rounded-lg shadow-sm focus:ring-2 focus:ring-blue-400 outline-none col-span-1 md:col-span-2 transition"
            rows={3}
          />

          {/* Custom Dropdown */}
          <div className="relative w-full">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              required
              className="appearance-none w-full p-3 border rounded-lg shadow-sm focus:ring-2 focus:ring-blue-400 outline-none bg-white transition"
            >
              <option value="">Select Category</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-3 flex items-center">
              <svg
                className="w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Availability & Featured */}
        <div className="flex flex-wrap gap-6">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={isAvailable}
              onChange={() => setIsAvailable(!isAvailable)}
              className="w-4 h-4 accent-blue-500"
            />
            Available
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={featured}
              onChange={() => setFeatured(!featured)}
              className="w-4 h-4 accent-blue-500"
            />
            Featured
          </label>
        </div>

        {/* Main Product Image Upload */}
        <div>
          <label className="block mb-2 font-semibold text-gray-700">Main Product Image</label>
          <div
            className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg p-4 cursor-pointer hover:border-blue-400 transition-colors"
            onClick={() => document.getElementById("mainImageInput").click()}
          >
            <input
              id="mainImageInput"
              type="file"
              accept="image/*"
              onChange={(e) => setImage(e.target.files[0])}
              className="hidden"
            />
            {preview ? (
              <img
                src={preview}
                alt="preview"
                className="w-32 h-32 object-cover rounded-lg shadow-md"
              />
            ) : (
              <p className="text-gray-400">Click or drag file to upload</p>
            )}
          </div>
        </div>

        {/* Variants */}
        {/* Variants */}
<div className="border-t pt-4">
  <h4 className="font-semibold text-lg mb-4">Variants</h4>

  {variants.map((variant, index) => (
    <motion.div
      key={index}
      className="relative border p-4 rounded-2xl mb-5 bg-gray-50 shadow hover:shadow-lg transition cursor-pointer"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      {/* Variant Header */}
      <div className="flex justify-between items-center mb-3">
        <h5 className="font-medium text-gray-800">{variant.variant_name || `Variant ${index + 1}`}</h5>
        <button
          type="button"
          onClick={() => removeVariant(index)}
          className="text-red-500 hover:text-red-600 text-sm font-medium"
        >
          Remove
        </button>
      </div>

      {/* Grid Inputs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-3">
        <input
          type="text"
          placeholder="Variant Name"
          value={variant.variant_name}
          onChange={(e) => handleVariantChange(index, "variant_name", e.target.value)}
          className="p-2 border rounded-lg shadow-sm focus:ring-2 focus:ring-blue-300 transition"
          required
        />
        <input
          type="text"
          placeholder="SKU (optional)"
          value={variant.sku}
          onChange={(e) => handleVariantChange(index, "sku", e.target.value)}
          className="p-2 border rounded-lg shadow-sm focus:ring-2 focus:ring-blue-300 transition"
        />
        <input
          type="number"
          placeholder="Base Price"
          value={variant.base_price}
          onChange={(e) => handleVariantChange(index, "base_price", e.target.value)}
          className="p-2 border rounded-lg shadow-sm focus:ring-2 focus:ring-blue-300 transition"
          required
        />
        <input
          type="number"
          placeholder="Offer Price"
          value={variant.offer_price}
          onChange={(e) => handleVariantChange(index, "offer_price", e.target.value)}
          className="p-2 border rounded-lg shadow-sm focus:ring-2 focus:ring-blue-300 transition"
        />
        <input
          type="number"
          placeholder="Stock"
          value={variant.stock}
          onChange={(e) => handleVariantChange(index, "stock", e.target.value)}
          className="p-2 border rounded-lg shadow-sm focus:ring-2 focus:ring-blue-300 transition"
          required
        />
      </div>

      {/* Return & Replacement Panel */}
      <div className="flex flex-wrap gap-4 items-center mb-3">
        {/* Return */}
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id={`allow-return-${index}`} // Unique ID per variant
            checked={variant.allow_return}
            onChange={(e) => handleVariantChange(index, "allow_return", e.target.checked)}
            className="w-4 h-4 accent-blue-500"
          />
          <label htmlFor={`allow-return-${index}`} className="cursor-pointer">
            Allow Return
          </label>

          {variant.allow_return && (
            <motion.input
              type="number"
              placeholder="Return Days"
              value={variant.return_days || ""}
              onChange={(e) => handleVariantChange(index, "return_days", e.target.value)}
              className="p-2 border rounded-lg w-32 shadow-sm focus:ring-2 focus:ring-blue-300 transition ml-2"
              min={1}
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
            />
          )}
        </div>

        {/* Replacement */}
        <div className="flex items-center gap-2">
          <input 
            type="checkbox"
            id={`allow-replacement-${index}`} // Unique ID per variant
            checked={variant.allow_replacement}
            onChange={(e) => handleVariantChange(index, "allow_replacement", e.target.checked)}
            className="w-4 h-4 accent-blue-500"
          />
          <label htmlFor={`allow-replacement-${index}`} className="cursor-pointer">
            Allow Replacement
          </label>

          {variant.allow_replacement && (
            <motion.input
              type="number"
              placeholder="Replacement Days"
              value={variant.replacement_days || ""}
              onChange={(e) => handleVariantChange(index, "replacement_days", e.target.value)}
              className="p-2 border rounded-lg w-32 shadow-sm focus:ring-2 focus:ring-blue-300 transition ml-2"
              min={1}
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
            />
          )}
        </div>
      </div>

      {/* Variant Image Upload */}
      <div>
        <label className="block mb-1 font-medium text-gray-700">Variant Images</label>
        <div
          className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg p-4 cursor-pointer hover:border-green-400 transition-colors"
          onClick={() => document.getElementById(`variantImageInput-${index}`).click()}
        >
          <input
            id={`variantImageInput-${index}`}
            type="file"
            accept="image/*"
            multiple
            onChange={(e) => handleVariantImages(index, e.target.files)}
            className="hidden"
          />
          {(variant.images.length || variant.existingImages.length) > 0 ? (
            <div className="flex flex-wrap gap-2 mt-2">
              {variant.images.map((file, i) => (
                <img
                  key={i}
                  src={URL.createObjectURL(file)}
                  alt="variant"
                  className="w-16 h-16 object-cover rounded-md border shadow"
                />
              ))}
              {variant.existingImages.map((url, i) => (
                <img
                  key={`existing-${i}`}
                  src={url}
                  alt="variant"
                  className="w-16 h-16 object-cover rounded-md border shadow"
                />
              ))}
            </div>
          ) : (
            <p className="text-gray-400">Click or drag files to upload</p>
          )}
        </div>
      </div>
    </motion.div>
  ))}

  <button
    type="button"
    onClick={addVariant}
    className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg shadow transition"
  >
    + Add Variant
  </button>
</div>


        {/* Submit */}
        <div className="flex justify-end gap-3 pt-4">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 transition"
          >
            Cancel
          </button>
          <motion.button
            type="submit"
            disabled={loading}
            whileTap={{ scale: 0.95 }}
            className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-lg transition"
          >
            {loading ? (isEdit ? "Updating..." : "Adding...") : isEdit ? "Update Product" : "Add Product"}
          </motion.button>
        </div>
      </form>
    </motion.div>
  </motion.div>
</AnimatePresence>

  );
};

export default AddProductModal;
