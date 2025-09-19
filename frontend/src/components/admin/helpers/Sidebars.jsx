import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import { FaChevronDown } from "react-icons/fa";

const Sidebars = ({label,icon:Icon,subLinks}) => {
  const [open, setOpen] = useState(false);

  return (
    <div>
      {/* Main link or group header */}
      <div
        onClick={() => subLinks && setOpen(!open)}
        className="flex items-center justify-between p-2 rounded hover:bg-gray-200 cursor-pointer"
      >
        <div className="flex items-center gap-2">
          {Icon && <Icon className="text-gray-600" />}
          <span className="hidden md:inline">{label}</span>
        </div>
        {subLinks && (
          <FaChevronDown
            className={`text-gray-500 transition-transform hidden md:inline ${
              open ? "rotate-180" : ""
            }`}
          />
        )}
      </div>

      {/* Sub-links (only visible when expanded) */}
      {open && subLinks && (
        <div className="ml-8 flex flex-col gap-1 mt-1">
          {subLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `block p-2 rounded text-sm ${
                  isActive ? "bg-blue-500 text-white" : "text-gray-700"
                }`
              }
            >
              {link.name}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  );
};

export default Sidebars