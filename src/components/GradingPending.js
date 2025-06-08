import React, { useEffect } from "react";
import { Loader2 } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "../api/axios";

const GradingPending = () => {
  const navigate = useNavigate();
  const { state } = useLocation();
  const subject = state?.subject;
  const examDate = state?.examDate;

  useEffect(() => {
    const interval = setInterval(() => {
      axios
        .get(`/images/check-status/${encodeURIComponent(subject)}`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        })
        .then((res) => {
          console.log("응답 데이터:", res.data);
          const { status, images } = res.data;

          if (status === "DONE") {
            clearInterval(interval);

            navigate("/review-answers", {
              state: {
                subject,
                examDate: state.examDate,
              },
            });
          }
        })
        .catch((err) => {
          console.error("채점 상태 확인 실패", err);
        });
    }, 3000);

    return () => clearInterval(interval);
  }, [navigate, subject]);

  return (
    <div className="flex items-center justify-center h-screen bg-white">
      <div className="flex flex-col items-center">
        <div className="flex items-center mb-4">
          <Loader2 className="animate-spin text-indigo-600 w-10 h-10 mr-4" />
          <h1 className="text-4xl font-extrabold">1차 인식 중입니다...</h1>
        </div>
        <p className="text-gray-600 text-lg">잠시만 기다려주세요.</p>
      </div>
    </div>
  );
};

export default GradingPending;
