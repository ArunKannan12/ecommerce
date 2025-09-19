// components/admin/AdminProducts.jsx
import React, { useState, useEffect } from "react";
import axiosInstance from "../../../api/axiosinstance";
import { toast } from "react-toastify";
import { motion } from "framer-motion";
import { FaEdit, FaTrash, FaPlus, FaImages } from "react-icons/fa";
import AddProductModal from "../modals/AddProductModal";
import EditProductModal from "../modals/EditProductModal.jsx";
import VariantModal from "../modals/VariantModal.jsx";
import VariantImagesModal from "../modals/VariantImagesModal.jsx";

// Modal imports


const AdminProducts = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedProduct, setSelectedProduct] = useState(null);

  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showVariantModal, setShowVariantModal] = useState(false);
  const [showImagesModal, setShowImagesModal] = useState(false);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const res = await axiosInstance.get("/products/", {
        params: { search: search || "" }, // send empty string if search is empty
      });
      setProducts(res.data.results);
      console.log(res.data.results);
    } catch (err) {
      console.error(err);
      const errMsg = err?.response?.data?.detail;
      toast.error(errMsg || "Failed to fetch products");
    }
    setLoading(false);
  };
  // Debounced fetch function
  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      fetchProducts();
    }, 500);

    return () => clearTimeout(delayDebounce);
  }, [search]);


  const handleDelete = async (slug) => {
    if (!window.confirm("Are you sure you want to delete this product?")) return;
    try {
      await axiosInstance.delete(`/products/${slug}/`);
      toast.success("Product deleted");
      setProducts((prev) => prev.filter((p) => p.slug !== slug)); // Optimistic update
    } catch (err) {
      toast.error("Failed to delete product");
    }
  };


  if (loading) return <p>Loading products...</p>;

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-800">Products</h2>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition"
        >
          <FaPlus /> Add Product
        </button>
      </div>

      <input
        type="text"
        placeholder="Search by name or description"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mb-4 w-full md:w-1/3 p-2 border rounded focus:outline-none focus:ring focus:ring-blue-200"
      />

      <div className="overflow-x-auto">
  <table className="w-full table-auto bg-white rounded-lg shadow">
    <thead className="bg-gray-200 text-gray-700">
      <tr>
        <th className="px-4 py-2">ID</th>
        <th className="px-4 py-2">Name</th>
        <th className="px-4 py-2">Category</th>
        <th className="px-4 py-2">Price</th>
        <th className="px-4 py-2">Stock</th>
        <th className="px-4 py-2">Actions</th>
      </tr>
    </thead>
    <tbody>
      {products.map((p, i) => {
        const totalStock = p.variants?.reduce((sum, v) => sum + v.stock, 0) || 0;
        const price = p.variants?.length
          ? Math.min(...p.variants.map((v) => v.final_price))
          : "-";
        return (
          <motion.tr
            key={p.slug}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="border-b hover:bg-gray-50"
          >
            <td className="px-4 py-2 text-center">{p.id}</td>
            <td className="px-4 py-2 flex items-center gap-2">
              {p.image_url && (
                <img
                  src={p.image_url}
                  alt={p.name}
                  className="w-10 h-10 object-cover rounded"
                />
              )}
              {p.name}
            </td>
            <td className="px-4 py-2">{p.category?.name || "-"}</td>
            <td className="px-4 py-2">₹{price}</td>
            <td className="px-4 py-2 text-center">{totalStock}</td>
            <td className="px-4 py-2 flex justify-center gap-2">
              <button
                onClick={() => {
                  setSelectedProduct(p);
                  setShowEditModal(true);
                }}
                className="text-blue-600 hover:text-blue-800"
              >
                <FaEdit />
              </button>
              <button
                onClick={() => handleDelete(p.slug)}
                className="text-red-600 hover:text-red-800"
              >
                <FaTrash />
              </button>
              <button
                onClick={() => {
                  setSelectedProduct(p);
                  setShowVariantModal(true);
                }}
                className="text-green-600 hover:text-green-800"
              >
                Variants
              </button>
              <button
                onClick={() => {
                  setSelectedProduct(p);
                  setShowImagesModal(true);
                }}
                className="text-purple-600 hover:text-purple-800"
              >
                <FaImages />
              </button>
            </td>
          </motion.tr>
        );
      })}
    </tbody>
  </table>
</div>


      {/* Modals */}
      {showAddModal && (
        <AddProductModal
          onClose={() => setShowAddModal(false)}
          onSuccess={fetchProducts}
        />
      )}
      {showEditModal && selectedProduct && (
        <EditProductModal
          product={selectedProduct}
          onClose={() => setShowEditModal(false)}
          onSuccess={fetchProducts}
        />
      )}
      {showVariantModal && selectedProduct && (
        <VariantModal
          product={selectedProduct}
          onClose={() => setShowVariantModal(false)}
        />
      )}
      {showImagesModal && selectedProduct && (
        <VariantImagesModal
          product={selectedProduct}
          onClose={() => setShowImagesModal(false)}
        />
      )}
    </div>
  );
};

export default AdminProducts;
