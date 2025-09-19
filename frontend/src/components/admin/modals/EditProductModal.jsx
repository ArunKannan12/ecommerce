// components/admin/modals/EditProductModal.jsx
import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import axiosInstance from "../../../api/axiosinstance";
import { toast } from "react-toastify";

const EditProductModal = ({ product, onClose, onSuccess }) => {
  const [name, setName] = useState(product.name);
  const [slug, setSlug] = useState(product.slug);
  const [description, setDescription] = useState(product.description);
  const [category, setCategory] = useState(product.category?.id || "");
  const [categories, setCategories] = useState([]);
  const [isAvailable, setIsAvailable] = useState(product.is_available);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const res = await axiosInstance.get("/categories/");
        setCategories(res.data);
      } catch (err) {
        toast.error("Failed to fetch categories");
      }
    };
    fetchCategories();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
     await axiosInstance.put(`/admin/products/${product.id}/`, {
        name,
        slug,
        description,
        category: parseInt(category),
        is_available: isAvailable,
      });
      toast.success("Product updated successfully");
      onSuccess();
      onClose();
    } catch (err) {
      toast.error("Failed to update product");
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <motion.div
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: -50, opacity: 0 }}
        className="bg-white rounded-xl p-6 w-full max-w-md shadow-lg relative"
      >
        <h3 className="text-xl font-bold mb-4">Edit Product</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="text"
            placeholder="Product Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full p-2 border rounded"
          />
          <input
            type="text"
            placeholder="Slug"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            required
            className="w-full p-2 border rounded"
          />
          <textarea
            placeholder="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full p-2 border rounded"
          />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            required
            className="w-full p-2 border rounded"
          >
            <option value="">Select Category</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={isAvailable}
              onChange={() => setIsAvailable(!isAvailable)}
            />
            Available
          </label>
          <div className="flex justify-end gap-2 mt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded bg-gray-300 hover:bg-gray-400"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600"
            >
              {loading ? "Updating..." : "Update Product"}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
};

export default EditProductModal;
