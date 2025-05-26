import React, { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "../api/axios";
import { Loader2 } from "lucide-react";

const StudentIdPending = () => {
  const navigate = useNavigate();
  const { state } = useLocation();
  const subject = state?.subject; // ✅ subject로 변경

  useEffect(() => {
    const interval = setInterval(() => {
      axios
        .get(`/exams/student-id-status?subject=${encodeURIComponent(subject)}`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        })
        .then((res) => {
          const { status, lowConfidenceIds } = res.data;

          if (status === "DONE") {
            clearInterval(interval);
            if (lowConfidenceIds && lowConfidenceIds.length > 0) {
              navigate("/review-low-confidence-ids", {
                state: { subject },
              });
            } else {
              navigate("/grading-pending", { state: { subject } });
            }
          }
        })
        .catch((err) => {
          console.error("학번 인식 상태 확인 실패", err);
        });
    }, 3000);

    return () => clearInterval(interval);
  }, [subject, navigate]);

  return (
    <div className="flex items-center justify-center h-screen bg-white">
      <div className="flex flex-col items-center">
        <div className="flex items-center mb-4">
          <Loader2 className="animate-spin text-indigo-600 w-10 h-10 mr-4" />
          <h1 className="text-4xl font-extrabold">학번 인식 중입니다...</h1>
        </div>
        <p className="text-gray-600 text-lg">출석부를 기반으로 학번을 분석 중입니다. 잠시만 기다려주세요.</p>
      </div>
    </div>
  );
};

export default StudentIdPending;
