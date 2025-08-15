import { toast } from "react-toastify";

export const syncGuestcart = async (mergeGuestCart, refetchCart) => {
  const localCart = JSON.parse(localStorage.getItem("cart")) || [];

  if (!Array.isArray(localCart) || localCart.length === 0) return true;

  try {
    const formattedItems = localCart.map(item => ({
      product_variant_id: item.product_variant_id,
      quantity: item.quantity,
    }));

    const response = await mergeGuestCart(formattedItems).unwrap();  // ✅ Pass array directly

    localStorage.removeItem("cart");

    const { merged_items, skipped_items, failed_items } = response;

    if (merged_items.length > 0) {
      toast.success(`${merged_items.length} items added to your cart`);
    }

    if (skipped_items.length > 0 || failed_items.length > 0) {
      toast.warn("Some items couldn't be added. Please review your cart.");
    }

    if (refetchCart) await refetchCart();

    return true;
  } catch (error) {
    toast.error("Failed to sync cart. Please try again.");
    return false;
  }
};
