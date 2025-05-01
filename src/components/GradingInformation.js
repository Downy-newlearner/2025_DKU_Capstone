import React, { useEffect, useState } from "react";
import axios from "../api/axios";
import { useNavigate } from "react-router-dom";
import { Button } from "./ui/button";

const GradingInformation = () => {
  const [data, setData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    axios
      .get("/exams/latest", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })
      .then((res) => {
        console.log("응답 데이터:", res.data); // ← 구조 확인용
        setData(res.data.data);  // ✅ 핵심 변경
      })
      .catch((err) => {
        console.error("정보 불러오기 실패:", err);
        alert("정보를 불러오지 못했습니다.");
      });
  }, []);

  if (!data) return <div className="p-10">Loading...</div>;

  return (
    <div className="max-w-4xl mx-auto p-10">
      <h1 className="text-3xl font-bold mb-6">제출한 시험 정보</h1>
      <div className="mb-4">
        <strong>시험 날짜:</strong> {data.exam_date}
      </div>
      <div className="mb-4">
        <strong>과목명:</strong> {data.subject}
      </div>
      <div className="mt-6">
        {data.questions.map((q, idx) => (
          <div key={idx} className="mb-4 p-4 border rounded shadow-sm">
            <div>
              <strong>
                {q.sub_question_number
                  ? `${q.question_number}(${q.sub_question_number})`
                  : `${q.question_number}`}
              </strong>
            </div>
            <div>유형: {q.question_type}</div>
            <div>답변: {q.answer}</div>
            <div>배점: {q.point}</div>
          </div>
        ))}
      </div>
      <Button className="mt-6" onClick={() => navigate("/main")}>메인으로</Button>
    </div>
  );
};

export default GradingInformation;
