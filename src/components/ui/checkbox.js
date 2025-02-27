import React from 'react';

export function Checkbox({ id, className, ...props }) {
  return (
    <input
      type="checkbox"
      id={id}
      className={`w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 ${className}`}
      {...props}
    />
  );
}
