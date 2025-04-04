import React from "react";

export const Separator = ({ orientation = "horizontal", className = "" }) => {
  const isHorizontal = orientation === "horizontal";

  return (
    <div
      className={`bg-black ${isHorizontal ? "h-0.5 w-full" : "w-full h-0.5"} ${className}`}
    />
  );
};


