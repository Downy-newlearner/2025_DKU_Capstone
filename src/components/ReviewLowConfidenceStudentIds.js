import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "../api/axios";
import { Button } from "./ui/button";
import { Input } from "./ui/input";

const ReviewLowConfidenceStudentIds = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const subject = state?.subject;
  const [entries, setEntries] = useState([]);

  useEffect(() => {
    if (!subject) return;

    axios
      .get(`/exams/low-confidence-student-ids?subject=${encodeURIComponent(subject)}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })
      .then((res) => {
        const prepared = res.data.student_list.map((item) => ({
          fileName: item.file_name,
          base64Data: item.base64_data[0], // 단일 문자열로 가정
          confirmedId: "",
        }));
        setEntries(prepared);
      })
      .catch((err) => {
        console.error("신뢰도 낮은 학번 이미지 불러오기 실패", err);
      });
  }, [subject]);

  const handleChange = (fileName, value) => {
    setEntries((prev) =>
      prev.map((entry) =>
        entry.fileName === fileName ? { ...entry, confirmedId: value } : entry
      )
    );
  };

  const handleSubmit = () => {
    const payload = {
      subject,
      student_list: entries.map(({ confirmedId, fileName }) => ({
        confirmed_id: confirmedId,
        file_name: fileName,
      })),
    };

    axios
      .post("http://13.209.197.61:8080/student/update-id", payload, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })
      .then(() => {
        navigate("/grading-pending", { state: { subject } });
      })
      .catch((err) => {
        console.error("학번 보정 제출 실패", err);
        alert("제출 중 오류가 발생했습니다.");
      });
  };

  return (
    <div className="bg-white flex flex-col items-center min-h-screen p-10">
      <h1 className="text-3xl font-bold mb-6">🧾 신뢰도 낮은 학번 확인</h1>

      <div className="grid gap-6 w-full max-w-4xl">
        {entries.map((entry, index) => (
          <div
            key={entry.fileName}
            className="flex items-center gap-6 border p-4 rounded shadow bg-white"
          >
            <div className="w-[200px] h-[200px] border flex items-center justify-center">
              <img
                src={`data:image/png;base64,${entry.base64Data}`}
                alt={`student-id-${index}`}
                className="max-w-full max-h-full object-contain"
              />
            </div>
            <div className="flex-grow">
              <Input
                placeholder="학번을 입력하세요"
                value={entry.confirmedId}
                onChange={(e) => handleChange(entry.fileName, e.target.value)}
              />
            </div>
          </div>
        ))}
      </div>

      {entries.length > 0 && (
        <Button
          className="mt-10 bg-[#c7aee7] hover:bg-[#b79dd6] text-white px-6 py-2 text-xl"
          onClick={handleSubmit}
        >
          제출하기
        </Button>
      )}
    </div>
  );
};

export default ReviewLowConfidenceStudentIds;
