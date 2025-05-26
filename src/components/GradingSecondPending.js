import React, { useEffect } from "react";
import { Loader2 } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";


const GradingSecondPending = () => {
  const navigate = useNavigate();
  const { state } = useLocation();
  const subject = state?.subject;

  useEffect(() => {
    const timer = setTimeout(() => {
      navigate("/grading-results", { state: { subject } }); // ✅ subject 전달
    }, 5000); // 5초 후 이동

    return () => clearTimeout(timer);
  }, [navigate, subject]);

  return (
    <div className="flex items-center justify-center h-screen bg-white">
      <div className="flex flex-col items-center">
        <div className="flex items-center mb-4">
          <Loader2 className="animate-spin text-indigo-600 w-10 h-10 mr-4" />
          <h1 className="text-4xl font-extrabold">2차 인식 중입니다...</h1>
        </div>
        <p className="text-gray-600 text-lg">잠시만 기다려주세요.</p>
      </div>
    </div>
  );
};

export default GradingSecondPending;
