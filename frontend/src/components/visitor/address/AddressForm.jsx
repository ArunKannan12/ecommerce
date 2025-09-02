import React, { useState, useEffect } from "react";

const AddressForm = ({ initialData = {}, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    full_name: "",
    address: "",
    postal_code: "",
    locality: "",
    city: "",
    district: "",
    state: "",
    country: "",
    phone_number: "",
    ...initialData,
  });

  const [localities, setLocalities] = useState([]);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  // Autofill city/state/locality when pincode changes
  useEffect(() => {
    const fetchLocation = async () => {
      const pin = formData.postal_code;
      if (pin && pin.length === 6) {
        try {
          const res = await fetch(`https://api.postalpincode.in/pincode/${pin}`);
          const data = await res.json();

          if (data[0].Status === "Success") {
            const offices = data[0].PostOffice || [];
            setLocalities(offices);

            const firstOffice = offices[0];
            setFormData((prev) => ({
              ...prev,
              locality: offices.length === 1 ? firstOffice.Name : "",
              city: firstOffice.Block || "",
              district: firstOffice.District || "",
              state: firstOffice.State || "",
              country: "India",
            }));
          } else {
            setLocalities([]);
          }
        } catch (err) {
          console.error("Pincode lookup failed:", err);
          setLocalities([]);
        }
      } else {
        setLocalities([]);
      }
    };
    fetchLocation();
  }, [formData.postal_code]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors({});
    setLoading(true);

    const result = await onSave(formData);

    if (result.success) {
      setErrors({});
      setLoading(false);
    } else {
      setErrors(result.errors);
      setLoading(false);
    }
  };


  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Display non-field errors */}
      {errors.non_field_errors && (
        <div className="text-red-600 text-sm">
          {errors.non_field_errors.join(", ")}
        </div>
      )}

      <input
        type="text"
        name="full_name"
        value={formData.full_name}
        onChange={handleChange}
        placeholder="Full Name"
        className="w-full border rounded px-3 py-2"
        required
      />
      {errors.full_name && <p className="text-red-600 text-xs">{errors.full_name.join(", ")}</p>}

      <textarea
        name="address"
        value={formData.address}
        onChange={handleChange}
        placeholder="Street Address"
        className="w-full border rounded px-3 py-2"
        required
      />
      {errors.address && <p className="text-red-600 text-xs">{errors.address.join(", ")}</p>}

      <input
        type="text"
        name="postal_code"
        value={formData.postal_code}
        onChange={handleChange}
        placeholder="Pincode"
        className="w-full border rounded px-3 py-2"
        required
      />
      {errors.postal_code && <p className="text-red-600 text-xs">{errors.postal_code.join(", ")}</p>}

      {localities.length > 1 ? (
        <select
          name="locality"
          value={formData.locality || ""}
          onChange={handleChange}
          className="w-full border rounded px-3 py-2"
          required
        >
          <option value="">Select Locality</option>
          {localities.map((loc, idx) => (
            <option key={idx} value={loc.Name}>
              {loc.Name}
            </option>
          ))}
        </select>
      ) : (
        <input
          type="text"
          name="locality"
          value={formData.locality || ""}
          onChange={handleChange}
          placeholder="Locality"
          className="w-full border rounded px-3 py-2"
          required
        />
      )}
      {errors.locality && <p className="text-red-600 text-xs">{errors.locality.join(", ")}</p>}

      <input type="text" name="city" value={formData.city} onChange={handleChange} placeholder="City" className="w-full border rounded px-3 py-2" required />
      {errors.city && <p className="text-red-600 text-xs">{errors.city.join(", ")}</p>}

      <input type="text" name="district" value={formData.district} onChange={handleChange} placeholder="District" className="w-full border rounded px-3 py-2" required />
      {errors.district && <p className="text-red-600 text-xs">{errors.district.join(", ")}</p>}

      <input type="text" name="state" value={formData.state} onChange={handleChange} placeholder="State" className="w-full border rounded px-3 py-2" required />
      {errors.state && <p className="text-red-600 text-xs">{errors.state.join(", ")}</p>}

      <input type="text" name="country" value={formData.country} onChange={handleChange} placeholder="Country" className="w-full border rounded px-3 py-2" required />
      {errors.country && <p className="text-red-600 text-xs">{errors.country.join(", ")}</p>}

      <input type="text" name="phone_number" value={formData.phone_number} onChange={handleChange} placeholder="Phone Number" className="w-full border rounded px-3 py-2" required />
      {errors.phone_number && <p className="text-red-600 text-xs">{errors.phone_number.join(", ")}</p>}

      <div className="flex justify-end gap-3">
        <button type="button" onClick={onCancel} className="px-4 py-2 text-gray-600 border rounded hover:bg-gray-100" disabled={loading}>
          Cancel
        </button>
        <button type="submit" className="px-4 py-2 text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50" disabled={loading}>
          {loading ? "Saving..." : "Save"}
        </button>
      </div>
    </form>
  );
};

export default AddressForm;
