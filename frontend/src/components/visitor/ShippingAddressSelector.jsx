import React from "react";

const ShippingAddressSelector = ({
  shippingAddresses=[],
  selectedAddressId,
  setSelectedAddressId,
  newAddress,
  setNewAddress,
}) => {
  return (
    <div className="mb-4">
      <h2 className="font-semibold mb-2">Shipping Address</h2>

      {/* Existing addresses */}
      {Array.isArray(shippingAddresses) && shippingAddresses.length > 0 ? (
        shippingAddresses.map((addr) => (
          <div key={addr.id} className="mb-2">
            <label className="flex items-center space-x-2">
              <input
                type="radio"
                name="selectedAddress"
                checked={selectedAddressId === addr.id}
                onChange={() => setSelectedAddressId(addr.id)}
              />
              <span>
                {addr.full_name}, {addr.address}, {addr.city}, {addr.postal_code}, {addr.country}
              </span>
            </label>
          </div>
        ))
      ) : (
        <p className="text-gray-500">No saved addresses</p>
      )}

      {/* Add new address */}
      <div className="mt-2 border p-4 rounded">
        <p className="font-semibold mb-2">Add New Address</p>
        {["full_name", "phone_number", "address", "city", "postal_code", "country"].map((field) => (
          <input
            key={field}
            type="text"
            placeholder={field.replace("_", " ").toUpperCase()}
            value={newAddress[field]}
            onChange={(e) => setNewAddress({ ...newAddress, [field]: e.target.value })}
            className="border p-2 mb-2 w-full"
          />
        ))}
      </div>
    </div>
  );
};

export default ShippingAddressSelector;
