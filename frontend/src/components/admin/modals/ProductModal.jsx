import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axiosInstance from "../../../api/axiosinstance.jsx";
import { toast } from "react-toastify";
import VariantForm from "./VariantForm.jsx";

const ProductModal = ({ onClose, onSuccess, product = null }) => {
  const isEdit = !!product;

  // ---------------- Product States ----------------
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [slugEdited, setSlugEdited] = useState(false);
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState([]);
  const [isAvailable, setIsAvailable] = useState(true);
  const [featured, setFeatured] = useState(false);
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [removeMainImage, setRemoveMainImage] = useState(false);
  const [loading, setLoading] = useState(false);

  // ---------------- Variants State ----------------
  const [variants, setVariants] = useState([]);

  // ---------------- Populate Fields for Edit ----------------
  useEffect(() => {
    if (!product) return;

    setName(product.name || "");
    setSlug(product.slug || "");
    setDescription(product.description || "");
    setCategory(product.category?.id || "");
    setIsAvailable(product.is_available ?? true);
    setFeatured(product.featured ?? false);
    setPreview(product.image_url || null);

    if (product.variants?.length) {
      setVariants(
        product.variants.map((v) => ({
          id: v.id,
          variant_name: v.variant_name,
          description: v.description || "",
          base_price: v.base_price,
          offer_price: v.offer_price || "",
          stock: v.stock,
          is_active: v.is_active ?? true,
          allow_return: v.allow_return ?? false,
          return_days: v.return_days || 0,
          allow_replacement: v.allow_replacement ?? false,
          replacement_days: v.replacement_days || 0,
          images: [],
          existingImages: v.images?.map(img=>img.image_url) || [],
        }))
      );
    } else {
      setVariants([
        {
          variant_name: "",
          description: "",
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
    }
  }, [product]);

  // ---------------- Auto-generate Slug ----------------
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

  // ---------------- Fetch Categories ----------------
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const res = await axiosInstance.get("/categories/");
        setCategories(
          res.data.results.sort((a, b) => a.name.localeCompare(b.name))
        );
      } catch (err) {
        toast.error(err?.response?.data?.detail || "Failed to fetch categories");
      }
    };
    fetchCategories();
  }, []);

  // ---------------- Preview Main Image ----------------
  useEffect(() => {
    if (!image) return;
    const objectUrl = URL.createObjectURL(image);
    setPreview(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [image]);

  // ---------------- Variant Handlers ----------------
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

  const handleRemoveVariantExistingImage = (variantIndex, imageIndex) => {
    const updated = [...variants];
    updated[variantIndex].existingImages.splice(imageIndex, 1);
    setVariants(updated);
  };

  const addVariant = () => {
    setVariants([
      ...variants,
      {
        variant_name: "",
        description: "",
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

  // ---------------- Handle Submit ----------------
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!name || !slug || !category)
      return toast.error("Name, slug, and category are required");
    if (!description.trim()) return toast.error("Description cannot be blank");

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("name", name);
      formData.append("slug", slug);
      formData.append("description", description);
      formData.append("category_id", Number(category));
      formData.append("is_available", isAvailable);
      formData.append("featured", featured);

      if (image) formData.append("image", image);
      if (isEdit && removeMainImage) formData.append("remove_image", true);

      const variantsPayload = variants.map((v) => ({
        id: v.id || null,
        variant_name: v.variant_name,
        description: v.description || description,
        base_price: v.base_price,
        offer_price: v.offer_price,
        stock: v.stock,
        is_active: v.is_active,
        allow_return: v.allow_return,
        return_days: v.return_days,
        allow_replacement: v.allow_replacement,
        replacement_days: v.replacement_days,
        existing_images: v.existingImages || [],
      }));
      formData.append("variants", JSON.stringify(variantsPayload));

      // Append new variant images
      variants.forEach((v, vIndex) =>
        v.images.forEach((file, imgIndex) =>
          formData.append(`variant_${vIndex}_image_${imgIndex}`, file)
        )
      );
      
      const url = isEdit
        ? `admin/products/${product.id}/`
        : "admin/create-products/";
      const method = isEdit ? "patch" : "post";

      await axiosInstance[method](url, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      toast.success(isEdit ? "Product updated" : "Product added");
      onSuccess();
      onClose();
    } catch (err) {
      console.error("❌ Axios Error:", err);
      toast.error(err?.response?.data?.detail || "Failed to save product");
    } finally {
      setLoading(false);
    }
  };

  // ---------------- Render ----------------
  return (
    <AnimatePresence>
      <motion.div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
        <motion.div
          initial={{ scale: 0.9, opacity: 0, y: -50 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.9, opacity: 0, y: -50 }}
          className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl p-6 overflow-y-auto max-h-[90vh]"
        >
          <h3 className="text-2xl font-bold mb-6 text-center text-gray-800">
            {isEdit ? "✏️ Edit Product" : "➕ Add Product"}
          </h3>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Product Fields */}
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="font-semibold">Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full border px-3 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
              </div>

              <div>
                <label className="font-semibold">Slug</label>
                <input
                  type="text"
                  value={slug}
                  onChange={(e) => {
                    setSlug(e.target.value);
                    setSlugEdited(true);
                  }}
                  className="w-full border px-3 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
              </div>

              <div className="md:col-span-2">
                <label className="font-semibold">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full border px-3 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
              </div>

              <div>
                <label className="font-semibold">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full border px-3 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
                >
                  <option value="">Select category</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-4">
                <label className="font-semibold">Available</label>
                <input
                  type="checkbox"
                  checked={isAvailable}
                  onChange={() => setIsAvailable(!isAvailable)}
                />
              </div>

              <div className="flex items-center gap-4">
                <label className="font-semibold">Featured</label>
                <input
                  type="checkbox"
                  checked={featured}
                  onChange={() => setFeatured(!featured)}
                />
              </div>

              <div className="md:col-span-2">
                <label className="font-semibold">Main Image</label>
                <input
                  type="file"
                  onChange={(e) => setImage(e.target.files[0])}
                  accept="image/*"
                  className="w-full"
                />
                {preview && (
                  <div className="mt-2 flex items-center gap-2">
                    <img
                      src={preview}
                      alt="Preview"
                      className="w-32 h-32 object-cover rounded-lg"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        setImage(null);
                        setPreview(null);
                        if (isEdit) setRemoveMainImage(true);
                      }}
                      className="px-2 py-1 bg-red-500 text-white rounded-lg text-sm"
                    >
                      Remove
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Variants */}
            <div className="border-t pt-4">
              <h4 className="font-semibold text-lg mb-4">Variants</h4>
              {variants.map((v, i) => (
                <VariantForm
                  key={i}
                  variant={v}
                  index={i}
                  onChange={handleVariantChange}
                  onRemove={removeVariant}
                  onImageChange={handleVariantImages}
                  onRemoveExistingImage={handleRemoveVariantExistingImage}
                />
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
                {loading
                  ? isEdit
                    ? "Updating..."
                    : "Adding..."
                  : isEdit
                  ? "Update Product"
                  : "Add Product"}
              </motion.button>
            </div>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default ProductModal;
