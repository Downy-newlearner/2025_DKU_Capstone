import React, { useEffect, useState } from "react";
import axios from "../api/axios";
import { useNavigate } from "react-router-dom";
import { Button } from "./ui/button";

const GradingInformation = () => {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null); // 💡 에러 상태 추가
  const navigate = useNavigate();
  // 유형 한글 변환 함수
  const getTypeLabel = (type, multiple) => {
    const map = {
      multiple_choice: "객관식",
      descriptive: "주관식",
      short_answer: "단답형",
      TF: "OX",
    };
    const base = map[type] || type;
    return (type === "multiple_choice" || type === "short_answer") && multiple
      ? `${base} (답 2개 이상)`
      : base;
  };

  const handleFinalSubmit = () => {
    axios.post("/exams/final", { examId: data.id }, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    })
    .then(() => {
      navigate("/grading-pending"); // ✅ 1차 채점 중 화면으로 이동
    })
    .catch(() => alert("제출 중 오류 발생"));
  };


  useEffect(() => {
    axios
      .get("/exams", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })
      .then((res) => {
        console.log("응답 데이터 구조 확인:", res.data); // 그대로 둬도 좋음
  
        const allExams = res.data;
        if (!Array.isArray(allExams) || allExams.length === 0) {
          throw new Error("응답 데이터가 비었습니다.");
        }
  
        const latest = allExams[allExams.length - 1]; // 가장 마지막 데이터 선택

        if (latest && Array.isArray(latest.questions)) {
          console.log("✅ 전체 문제 목록:", latest.questions.map(q => ({
            question_number: q.question_number,
            sub_question_number: q.sub_question_number
          })));
        }
        setData(latest);
      })
      .catch((err) => {
        console.error("정보 불러오기 실패:", err);
        setError("시험 정보를 불러오지 못했습니다.");
      });
  }, []);
  
  if (error) return <div className="p-10 text-red-500">{error}</div>;
  if (!data) return <div className="p-10">Loading...</div>;

  return (
    <div className="bg-white flex flex-row justify-center w-full min-h-screen">
      <div className="bg-white w-full max-w-[1440px] h-[900px] relative">
        {/* 로그아웃 + 로고 */}
        <div className="absolute top-[29px] right-[35px]">
          <Button
            variant="link"
            className="font-normal text-xl text-black"
            onClick={() => {
              const confirmLogout = window.confirm("로그아웃하시겠습니까?");
              if (confirmLogout) {
                localStorage.removeItem("token");
                navigate("/");
              }
            }}
          >
            Logout
          </Button>
        </div>
        <button
          className="absolute w-32 h-[30px] top-[29px] left-[52px]"
          onClick={() => navigate("/main")}
        >
          <img src="/Checkmate5.png" alt="CheckMate Logo" className="w-full h-full object-cover" />
        </button>

        <div className="max-w-4xl mx-auto p-10">
          <h1 className="text-3xl font-bold mb-6">제출한 시험 정보</h1>
          <div className="mb-4">
            <strong>시험 날짜:</strong> {data.exam_date}
          </div>
          <div className="mb-4">
            <strong>과목명:</strong> {data.subject}
          </div>
          <div className="mt-6">
            {data.questions
            // 꼬리문제가 존재하는 메인문제는 렌더링에서 제외
            .filter(q =>
              !(
                q.sub_question_number === 0 &&
                data.questions.some(
                  sub =>
                    sub.question_number === q.question_number &&
                    sub.sub_question_number !== 0
                )
              )
            ).map((q, idx) => {
              // 객관식 또는 단답형에서 답이 2개 이상인지 확인
                const isMultipleAnswer =
                  (q.question_type === "multiple_choice" || q.question_type === "short_answer") &&
                  typeof q.answer === "string" &&
                  q.answer.includes(",");

                return (
                  <div key={idx} className="mb-4 p-4 border rounded shadow-sm">
                    <div>
                      <strong>
                        {q.sub_question_number
                          ? `${q.question_number}(${q.sub_question_number})`
                          : `${q.question_number}`}
                      </strong>
                    </div>
                    <div>유형: {getTypeLabel(q.question_type, isMultipleAnswer)}</div>
                    <div>답변: {q.answer}</div>
                    <div>배점: {q.point}</div>
                  </div>
                );
              })}
          </div>
          <div className="flex gap-4 mt-6">
            <Button
              className="bg-[#f2bcbc] hover:bg-[#e1a9a9] text-white text-xl px-4 py-2 rounded"
              onClick={() => navigate("/grading", { state: data })}
            >
              수정하기
            </Button>
            <Button
              className="bg-[#c7aee7] hover:bg-[#b79dd6] text-white text-xl px-4 py-2 rounded"
              onClick={handleFinalSubmit}
            >
              최종 제출
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GradingInformation;
