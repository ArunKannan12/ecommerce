import { useState,useEffect } from 'react';
import { Tabs, Tab } from 'react-bootstrap';
import ProfileEditModal from './ProfileEditModal';
import { useAuth } from '../../contexts/authContext';


const Profile = () => {
  const { user, setUser, loading } = useAuth();
  const [showModal, setShowModal] = useState(false);
    const [location, setLocation] = useState(null);
const [loadingLocation, setLoadingLocation] = useState(true);


  if (loading || !user) {
    return (
      <div className="d-flex justify-content-center align-items-center min-vh-100">
        <span>Loading profile...</span>
      </div>
    );
  }

  const profilePic =
    user.custom_user_profile ||
    user.social_auth_pro_pic ||
    'https://cdn-icons-png.flaticon.com/512/149/149071.png';
  const ip = user.last_login_ip
useEffect(() => {
  if (ip) {
    const fetchGeoLocation = async () => {
      try {
        const res = await fetch(`https://ipapi.co/${ip}/json/`);
        const data = await res.json();
        setLocation({
          city: data.city,
          region: data.region,
          country: data.country_name,
        });
      } catch (err) {
        console.error("Geo lookup failed", err);
      } finally {
        setLoadingLocation(false);
      }
    };
    fetchGeoLocation();
  }
}, [ip]);



  return (
    <div className="max-w-4xl mx-auto py-12 px-6 bg-white rounded-xl shadow-lg border border-gray-200">
  {/* Header */}
  <div className="max-w-4xl mx-auto py-10 px-6 bg-white rounded-xl shadow-md border border-gray-200">
  {/* Profile Header */}
  <div className="text-center mb-8">
    <div className="relative inline-block">
        <img
            src={profilePic}
            alt="Profile"
            className="rounded-full border-4 border-white shadow-lg object-cover"
            style={{ width: 120, height: 120 }}
            referrerPolicy="no-referrer"
            onError={(e) => {
            e.target.onerror = null;
            e.target.src = "/default-avatar.png";
            }}
        />

        {/* Floating Edit Button */}
        <button
            className="absolute bottom-0 right-0 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-xs px-3 py-1 rounded-full shadow hover:scale-105 transition-transform"
            onClick={() => setShowModal(true)}
        >
            ✏️ Edit
        </button>
        </div>
    <h2 className="mt-4 text-2xl font-bold text-gray-800">
      {user.first_name} {user.last_name}
    </h2>
    <p className="text-gray-500 text-sm">{user.email}</p>
    <span className="inline-block mt-2 px-4 py-1 bg-gray-700 text-white text-xs rounded-full uppercase tracking-wide">
      {user.role}
    </span>
    <p className="text-xs text-gray-400 mt-1 italic">
      Signed in via {user.auth_provider}
    </p>
    <div className="text-center mt-4">

</div>
  </div>

  {/* Info Grid */}
  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-700">
    <div>
      <h5 className="text-lg font-semibold text-gray-900 mb-2">📞 Contact Info</h5>
      <p className="bg-gray-50 p-3 rounded border">{user.phone_number || 'Not provided'}</p>
    </div>
    <div>
      <h5 className="text-lg font-semibold text-gray-900 mb-2">🏠 Address</h5>
      <p className="bg-gray-50 p-3 rounded border">
        {user.address
          ? `${user.address}, ${user.city}, ${user.district}, ${user.state} - ${user.pincode}`
          : 'No address saved'}
      </p>
    </div>
    <div>
      <h5 className="text-lg font-semibold text-gray-900 mb-2">📅 Member Since</h5>
      <p className="bg-gray-50 p-3 rounded border">
        {new Date(user.created_at).toLocaleDateString("en-IN", {
          year: "numeric",
          month: "long",
          day: "numeric",
        })}
      </p>
    </div>
    <div>
      <h5 className="text-lg font-semibold text-gray-900 mb-2">🕒 Last Login IP</h5>
      {loadingLocation ? (
        <span>Detecting location...</span>
        ) : location ? (
        <span>{location.city}, {location.region}, {location.country}</span>
        ) : (
        <span>Location unavailable</span>
        )}

    </div>
  </div>
</div>

  {/* Modal */}
  <ProfileEditModal
    show={showModal}
    onHide={() => setShowModal(false)}
    user={user}
    setUser={setUser}
  />
</div>
  );
};

export default Profile;