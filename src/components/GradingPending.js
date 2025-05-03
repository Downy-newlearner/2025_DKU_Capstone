import React, { useEffect } from "react";
import { Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";

const GradingPending = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      navigate("/result1"); // 채점 완료 후 결과 페이지로 이동
    }, 5000);
    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className="flex items-center justify-center h-screen bg-white">
      <div className="flex flex-col items-center">
        <div className="flex items-center mb-4">
        <Loader2 className="animate-spin text-indigo-600 w-10 h-10 mr-4" />
        <h1 className="text-4xl font-extrabold">1차 채점 중입니다...</h1>
        </div>
        <p className="text-gray-600 text-lg">잠시만 기다려주세요.</p>
      </div>
    </div>
  );
};

export default GradingPending;
