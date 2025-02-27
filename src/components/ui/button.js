import React from 'react';

export function Button({ children, className, ...props }) {
  return (
    <button
      className={`bg-black text-white py-2 px-4 rounded-lg hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
