import React, { useEffect } from "react";
import { Loader2 } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "../api/axios";

const GradingPending = () => {
  const navigate = useNavigate();
  const { state } = useLocation(); // examId를 state로부터 받음

  useEffect(() => {
    const interval = setInterval(() => {
      axios
        .get(`/exams/check-status?examId=${state.examId}`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        })
        .then((res) => {
          const { status, lowConfidence } = res.data;

          if (status === "DONE") {
            clearInterval(interval); // polling 중지

            if (lowConfidence && lowConfidence.length > 0) {
              navigate("/review-answers", {
                state: { images: lowConfidence },
              });
            } else {
              navigate("/result1", { state: { examId: state.examId } });
            }
          }
        })
        .catch((err) => {
          console.error("채점 상태 확인 실패", err);
        });
    }, 3000); // 3초마다 polling

    return () => clearInterval(interval);
  }, [navigate, state.examId]);

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
