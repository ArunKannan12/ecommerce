import React, { useEffect, useState } from "react";
import axiosInstance from "../../api/axiosinstance";
import { toast } from "react-toastify";

const ShippingAddressSelector = ({ selectedAddress, setSelectedAddress }) => {
  const [shippingAddresses, setShippingAddresses] = useState([]);
  const [newAddress, setNewAddress] = useState({
      full_name: "",
      phone_number: "",
      address: "",
      city: "",
      postal_code: "",
      country: "",
      state: "",
      district: "",   // ✅ Add this
      region: ""      // ✅ Add this
    });
  const [editAddressId, setEditAddressId] = useState(null);
  const [editAddressData, setEditAddressData] = useState({});
  const [postOfficeOptions, setPostOfficeOptions] = useState([]);
  const [selectedLocality, setSelectedLocality] = useState("");

  const isUsingNewAddress = !selectedAddress;

  useEffect(() => {
    fetchAddresses();
  }, []);

  useEffect(() => {
    const fetchPincodeDetails = async () => {
      const pin = newAddress.postal_code;
      if (pin.length === 6 && /^\d{6}$/.test(pin)) {
        try {
          const res = await fetch(`https://api.postalpincode.in/pincode/${pin}`);
          const data = await res.json();
          const postOffices = data[0]?.PostOffice;

          if (postOffices?.length) {
            setPostOfficeOptions(postOffices);
            setSelectedLocality(postOffices[0].Name);
           setNewAddress((prev) => ({
              ...prev,
              city: postOffices[0].District || prev.city,
              country: postOffices[0].Country || "India",
              state: postOffices[0].State || "",
              district: postOffices[0].District || "",
              region: postOffices[0].Block || ""
            }));
          } else {
            setPostOfficeOptions([]);
            setSelectedLocality("");
            toast.warn("No location data found for this pincode");
          }
        } catch (err) {
          console.error("Pincode lookup failed:", err);
          toast.error("Failed to fetch location from pincode");
        }
      }
    };

    fetchPincodeDetails();
  }, [newAddress.postal_code]);

  const fetchAddresses = async () => {
    try {
      const res = await axiosInstance.get("shipping-addresses/");
      const addresses = res.data.results || [];
      setShippingAddresses(addresses);
      if (addresses.length && !selectedAddress) {
        setSelectedAddress(addresses[0]);
      }
    } catch {
      toast.error("Failed to load shipping addresses");
    }
  };

  const handleEdit = (addr) => {
    setEditAddressId(addr.id);
    setEditAddressData({ ...addr });
  };

  const handleEditSubmit = async () => {
    try {
      await axiosInstance.put(`shipping-addresses/${editAddressId}/`, editAddressData);
      toast.success("Address updated");
      setEditAddressId(null);
      fetchAddresses();
    } catch {
      toast.error("Failed to update address");
    }
  };

  const handleDelete = async (id) => {
    try {
      await axiosInstance.delete(`shipping-addresses/${id}/`);
      toast.success("Address deleted");
      fetchAddresses();
    } catch (err) {
      console.error("Delete failed:", err.response?.data || err.message);
      toast.error("Failed to delete address");
    }
  };

  const handleAddNewAddress = async () => {
      try {
        const payload = {
          ...newAddress,
          locality: selectedLocality,
        };
        console.log("Payload being sent:", payload);

        const res = await axiosInstance.post("shipping-addresses/", payload);
        toast.success("Address added");
        setSelectedAddress(res.data);
        setNewAddress({
          full_name: "",
          phone_number: "",
          address: "",
          city: "",
          postal_code: "",
          country: "",
          state: "",
          district: "",
          region: ""
        });
        setPostOfficeOptions([]);
        setSelectedLocality("");
        fetchAddresses();
      } catch (err) {
        const errorMsg =
          err.response?.data?.message ||
          err.response?.data?.detail ||
          JSON.stringify(err.response?.data) ||
          "Failed to add address";

        console.error("Address creation failed:", err.response?.data);
        toast.error(`Error: ${errorMsg}`);
      }
    };

  return (
    <div className="mb-8">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">Shipping Address</h2>

      {shippingAddresses.length > 0 && (
        <>
          {shippingAddresses.map((addr) => (
            <div
              key={addr.id}
              className={`border rounded-lg p-4 mb-4 shadow-sm transition ${
                selectedAddress?.id === addr.id ? "border-blue-500 bg-blue-50" : "border-gray-300"
              }`}
            >
              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="radio"
                  name="selectedAddress"
                  checked={selectedAddress?.id === addr.id}
                  onChange={() => setSelectedAddress(addr)}
                  className="mt-1 accent-blue-600"
                />
                <div className="flex-1 text-sm text-gray-700">
                  {editAddressId === addr.id ? (
                    <>
                      {["full_name", "phone_number", "address", "city", "postal_code", "country", "state"].map(
                        (field) => (
                          <input
                            key={field}
                            type="text"
                            value={editAddressData[field]}
                            onChange={(e) =>
                              setEditAddressData({ ...editAddressData, [field]: e.target.value })
                            }
                            placeholder={field.replace("_", " ").toUpperCase()}
                            className="border p-2 mb-2 w-full rounded text-sm"
                          />
                        )
                      )}
                      <div className="flex gap-3 mt-2">
                        <button
                          onClick={handleEditSubmit}
                          className="px-3 py-1 text-sm text-white bg-green-600 rounded hover:bg-green-700"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setEditAddressId(null)}
                          className="px-3 py-1 text-sm text-gray-700 bg-gray-200 rounded hover:bg-gray-300"
                        >
                          Cancel
                        </button>
                      </div>
                    </>
                  ) : (
                    <>
                      <p>
                        {addr.full_name}, {addr.address}, {addr.city}, {addr.postal_code}, {addr.state},{" "}
                        {addr.country}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">{addr.phone_number}</p>
                      <div className="flex gap-4 mt-2">
                        <button
                          onClick={() => handleEdit(addr)}
                          className="text-blue-600 text-sm hover:underline"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(addr.id)}
                          className="text-red-500 text-sm hover:underline"
                        >
                          Delete
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </label>
            </div>
          ))}

          <div className="mb-4 p-3 rounded border border-gray-300">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="radio"
                name="selectedAddress"
                checked={isUsingNewAddress}
                onChange={() => setSelectedAddress(null)}
                className="accent-blue-600"
              />
              <span className="text-sm text-gray-800">Use a new address</span>
            </label>
          </div>
        </>
      )}

      <div
        className={`p-4 rounded-lg border ${
          isUsingNewAddress ? "border-blue-500 bg-blue-50" : "border-gray-300 bg-gray-50"
        }`}
      >
        <p className="font-semibold mb-3 text-sm text-gray-700">Add New Address</p>
        {["full_name", "phone_number", "address", "postal_code"].map((field) => (
          <input
            key={field}
            type="text"
            placeholder={field.replace("_", " ").toUpperCase()}
            value={newAddress[field]}
            onChange={(e) => setNewAddress({ ...newAddress, [field]: e.target.value })}
            disabled={!isUsingNewAddress}
            className={`border p-2 mb-2 w-full rounded text-sm ${
              isUsingNewAddress ? "bg-white" : "bg-gray-200 cursor-not-allowed"
            }`}
          />
        ))}

        {postOfficeOptions.length > 0 && isUsingNewAddress && (
          <select
            value={selectedLocality}
            onChange={(e) => setSelectedLocality(e.target.value)}
            className="border p-2 mb-2 w-full rounded text-sm bg-white"
          >
            {postOfficeOptions.map((office) => (
              <option key={office.Name} value={office.Name}>
                {office.Name} ({office.Block}, {office.District})
              </option>
            ))}
          </select>
        )}

                {["city", "state", "country","district","region"].map((field) => (
          <input
            key={field}
            type="text"
            placeholder={field.toUpperCase()}
            value={newAddress[field]}
            onChange={(e) => setNewAddress({ ...newAddress, [field]: e.target.value })}
            disabled={!isUsingNewAddress}
            className={`border p-2 mb-2 w-full rounded text-sm ${
              isUsingNewAddress ? "bg-white" : "bg-gray-200 cursor-not-allowed"
            }`}
          />
        ))}

        {isUsingNewAddress && (
          <button
            onClick={handleAddNewAddress}
            className="mt-2 px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700"
          >
            Add Address
          </button>
        )}
      </div>
    </div>
  );
};

export default ShippingAddressSelector;