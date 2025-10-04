import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import axiosInstance from "../../../api/axiosinstance";
import { toast } from "react-toastify";
import BannerConfirmDelete from "../helpers/BannerConfirmDelete";

const BannerFormModal = ({ banner, onClose, refreshBanners }) => {
  const [title, setTitle] = useState(banner.title || "");
  const [subtitle, setSubtitle] = useState(banner.subtitle || "");
  const [linkUrl, setLinkUrl] = useState(banner.link_url || "");
  const [order, setOrder] = useState(banner.order || 0);
  const [isActive, setIsActive] = useState(banner.is_active);
  const [imageFile, setImageFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Update modal state when banner prop changes
  useEffect(() => {
    setTitle(banner.title || "");
    setSubtitle(banner.subtitle || "");
    setLinkUrl(banner.link_url || "");
    setOrder(banner.order || 0);
    setIsActive(banner.is_active || false);
  }, [banner]);

  const handleUpdate = async () => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("title", title);
      formData.append("subtitle", subtitle);
      formData.append("link_url", linkUrl);
      formData.append("order", order);
      formData.append("is_active", isActive);
      if (imageFile) formData.append("image", imageFile);

      await axiosInstance.patch(`admin/banners/${banner.id}/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      toast.success("Banner updated successfully");
      refreshBanners();
      onClose();
    } catch (err) {
        console.log(err);
        
      toast.error(err.response?.data?.detail || "Failed to update banner");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    setLoading(true);
    try {
      await axiosInstance.delete(`admin/banners/${banner.id}/`);
      toast.success("Banner deleted successfully");
      refreshBanners();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to delete banner");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 sm:p-6"
    >
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: -20, opacity: 0 }}
        className="bg-white rounded-lg w-full max-w-md sm:max-w-lg lg:max-w-xl p-4 sm:p-6 md:p-8 relative overflow-y-auto max-h-[90vh]"
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-500 hover:text-gray-700 text-lg"
        >
          ✕
        </button>

        <h2 className="text-lg sm:text-xl md:text-2xl font-semibold mb-4">
          Edit Banner
        </h2>

        <motion.div
          initial="hidden"
          animate="visible"
          exit="hidden"
          variants={{
            visible: { transition: { staggerChildren: 0.08 } },
          }}
          className="space-y-3"
        >
          {[
            { label: "Title", value: title, setter: setTitle, type: "text" },
            { label: "Subtitle", value: subtitle, setter: setSubtitle, type: "text" },
            { label: "Order", value: order, setter: setOrder, type: "number" },
          ].map((field, idx) => (
            <motion.div
              key={idx}
              className="flex flex-col"
              variants={{ hidden: { opacity: 0, y: -5 }, visible: { opacity: 1, y: 0 } }}
            >
              <label className="block font-medium text-sm sm:text-base">{field.label}</label>
              <input
                type={field.type}
                value={field.value}
                onChange={(e) =>
                  field.setter(field.type === "number" ? Number(e.target.value) : e.target.value)
                }
                className="w-full border rounded px-2 py-1 sm:px-3 sm:py-2 focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </motion.div>
          ))}

          {/* Active Checkbox */}
          <motion.div
            className="flex items-center gap-2 text-sm sm:text-base"
            variants={{ hidden: { opacity: 0, y: -5 }, visible: { opacity: 1, y: 0 } }}
          >
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
            />
            <span>Active</span>
          </motion.div>

          {/* Image Upload */}
          <motion.div
            className="flex flex-col gap-2"
            variants={{ hidden: { opacity: 0, y: -5 }, visible: { opacity: 1, y: 0 } }}
          >
            <label className="block font-medium text-sm sm:text-base">Banner Image</label>
            {banner.image_url && (
              <img
                src={imageFile ? URL.createObjectURL(imageFile) : banner.image_url}
                alt={title}
                className="w-full h-40 object-contain rounded border"
              />
            )}
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setImageFile(e.target.files[0])}
              className="w-full"
            />
          </motion.div>

          {/* Buttons */}
          <motion.div
            className="flex flex-col sm:flex-row justify-between gap-2 mt-4"
            variants={{ hidden: { opacity: 0, y: -5 }, visible: { opacity: 1, y: 0 } }}
          >
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="bg-red-500 text-white px-4 py-2 rounded"
              disabled={loading}
            >
              Delete
            </button>
            <button
              onClick={handleUpdate}
              className="bg-indigo-500 text-white px-4 py-2 rounded w-full sm:w-auto"
              disabled={loading}
            >
              Save
            </button>
          </motion.div>
        </motion.div>
      </motion.div>

      {/* Delete confirmation modal */}
      <BannerConfirmDelete
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={() => {
          handleDelete();
          setShowDeleteConfirm(false);
        }}
        message="Are you sure you want to delete this banner? This action cannot be undone."
      />
    </motion.div>
  );
};

export default BannerFormModal;
