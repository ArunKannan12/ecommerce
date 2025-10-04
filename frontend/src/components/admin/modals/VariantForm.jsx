import React, { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

const VariantForm = ({
  variant,
  index,
  onChange,
  onRemove,
  onImageChange,
  onRemoveExistingImage,
}) => {
  const objectUrlsRef = useRef([]);
  const [previewImages, setPreviewImages] = useState([]);

  // Update previews for newly uploaded images
  useEffect(() => {
    // Clean old URLs
    objectUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
    objectUrlsRef.current = [];

    const urls = variant.images.map((file) => {
      const url = URL.createObjectURL(file);
      objectUrlsRef.current.push(url);
      return url;
    });

    setPreviewImages(urls);

    return () => objectUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
  }, [variant.images]);

  const handleChange = (field, value) => {
    onChange(index, field, value);
  };

  const handleFiles = (files) => {
    onImageChange(index, Array.from(files));
  };

  return (
    <motion.div
      className="relative border p-4 rounded-2xl mb-5 bg-gray-50 shadow hover:shadow-lg transition"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      {/* Header */}
      <div className="flex justify-between items-center mb-3">
        <h5 className="font-medium text-gray-800">
          {variant.variant_name || `Variant ${index + 1}`}
        </h5>
        <button
          type="button"
          onClick={() => onRemove(index)}
          className="text-red-500 text-sm font-medium"
        >
          Remove
        </button>
      </div>

      {/* Variant Fields */}
      <div className="grid md:grid-cols-2 gap-4 mb-4">
        {["variant_name", "description", "base_price", "offer_price", "stock"].map((field) => (
          <div key={field}>
            <label className="font-semibold">{field.replace("_", " ").toUpperCase()}</label>
            <input
              type={field.includes("price") || field === "stock" ? "number" : "text"}
              value={variant[field]}
              onChange={(e) => handleChange(field, e.target.value)}
              className="w-full border px-3 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>
        ))}
      </div>

      {/* Variant Images */}
      <div>
        <label className="block mb-1 font-medium text-gray-700">Variant Images</label>
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={(e) => handleFiles(e.target.files)}
          className="mb-2"
        />

        <div className="flex flex-wrap gap-2 mt-2">
          {/* New uploads */}
          {previewImages.map((src, i) => (
            <div key={`new-${i}`} className="relative">
              <img src={src} className="w-16 h-16 object-cover rounded-md border shadow" />
              <button
                type="button"
                onClick={() => {
                  const newFiles = [...variant.images];
                  newFiles.splice(i, 1);
                  onImageChange(index, newFiles);
                }}
                className="absolute top-0 right-0 bg-red-500 text-white rounded-full w-5 h-5 text-xs flex items-center justify-center"
              >
                ×
              </button>
            </div>
          ))}

          {/* Existing images */}
          {variant.existingImages.map((img, i) => (
            <div key={`existing-${i}`} className="relative">
              <img
                src={img.url || img}
                className="w-16 h-16 object-cover rounded-md border shadow"
              />
              <button
                type="button"
                onClick={() => onRemoveExistingImage(index, i)}
                className="absolute top-0 right-0 bg-red-500 text-white rounded-full w-5 h-5 text-xs flex items-center justify-center"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default VariantForm;
