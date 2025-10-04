// components/admin/modals/CategoryModal.jsx
import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import axiosInstance from "../../../api/axiosinstance";
import { FaTimes, FaTrash } from "react-icons/fa";

const CategoryModal = ({ category = null, onClose, onSuccess }) => {
  const isEdit = !!category;

  const [name, setName] = useState(category?.name || "");
  const [slug, setSlug] = useState(category?.slug || "");
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(category?.image_url || null);
  const [removeImage, setRemoveImage] = useState(false); // flag to remove existing image
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isEdit) {
      setSlug(name.toLowerCase().replace(/\s+/g, "-"));
    }
  }, [name, isEdit]);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      setPreview(URL.createObjectURL(file));
      setRemoveImage(false); // undo remove if new image selected
    }
  };

  const handleRemoveImage = () => {
    setImage(null);
    setPreview(null);
    setRemoveImage(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !slug.trim()) {
      toast.error("Name and slug are required");
      return;
    }

    setLoading(true);
    try {
      if (isEdit) {
        if (image || removeImage) {
          // --- use FormData when touching image ---
          const formData = new FormData();
          formData.append("name", name);
          formData.append("slug", slug);
          if (image) formData.append("image", image);
          if (removeImage) formData.append("remove_image", "true");

          await axiosInstance.patch(`/categories/${category.slug}/`, formData, {
            headers: { "Content-Type": "multipart/form-data" },
          });
        } else {
          // --- just send JSON if no image updates ---
          await axiosInstance.patch(`/categories/${category.slug}/`, {
            name,
            slug,
          });
        }
        toast.success("Category updated successfully");
      } else {
        // --- always FormData when creating, since image might be included ---
        const formData = new FormData();
        formData.append("name", name);
        formData.append("slug", slug);
        if (image) formData.append("image", image);

        await axiosInstance.post("/categories/", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });

        toast.success("Category added successfully");
      }

      onSuccess();
      onClose();
    } catch (err) {
      console.error(err);
      toast.error(
        err?.response?.data?.detail || "Failed to save category"
      );
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
        >
          <FaTimes />
        </button>

        <h2 className="text-2xl font-bold mb-4">{isEdit ? "Edit Category" : "Add Category"}</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-400 outline-none"
              placeholder="Category name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Slug</label>
            <input
              type="text"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-400 outline-none"
              placeholder="category-slug"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Image</label>
            <input type="file" accept="image/*" onChange={handleImageChange} />
            {preview && (
              <div className="mt-2 flex items-center gap-2">
                <img src={preview} alt="Preview" className="w-32 h-32 object-cover rounded-md border" />
                <button
                  type="button"
                  onClick={handleRemoveImage}
                  className="text-red-600 hover:text-red-800 flex items-center gap-1"
                >
                  <FaTrash /> Remove
                </button>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 mt-4">
            <button type="button" onClick={onClose} className="px-4 py-2 border rounded-lg hover:bg-gray-100">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              {loading ? "Saving..." : isEdit ? "Update" : "Add"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CategoryModal;
