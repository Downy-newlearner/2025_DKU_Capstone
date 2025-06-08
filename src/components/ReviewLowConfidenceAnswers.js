import React, { useEffect, useState } from "react";
import axios from "../api/axios";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { useLocation, useNavigate } from "react-router-dom";


const ReviewLowConfidenceAnswers = () => {
  const navigate = useNavigate();
  const { state } = useLocation(); // state.subject 를 전달받았다고 가정
  const subject = state?.subject || "알 수 없음";
  const [examDate, setExamDate] = useState("알 수 없음");

  const [images, setImages] = useState([]);

  useEffect(() => {
    if (!subject) return;

    axios
      .get(`/images/${subject}/low-confidence`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })
      .then((res) => {
        console.log("불러온 이미지 목록:", res.data);
        setExamDate(res.data.exam_date);

        const dataWithAnswer = res.data.images.map((item, i) => {
          console.log(`[${i}] 받은 item:`, item); 
          const rawQ = item.question_number;
          const rawSubQ = item.sub_question_number;

          const parsedQ = Number(rawQ);
          const parsedSubQ = Number(rawSubQ || 0);

          return {
            ...item,
            base64Data: item.base64_data,
            answer: "",
            student_id: String(item.student_id),
            questionNumber: isNaN(parsedQ) ? undefined : parsedQ,
            subQuestionNumber: isNaN(parsedSubQ) ? 0 : parsedSubQ,
          };
        });
        setImages(dataWithAnswer);
        console.log("student_id 값:", dataWithAnswer[0].student_id);
        console.log("student_id 타입:", typeof dataWithAnswer[0].student_id);
      })
      .catch((err) => console.error("이미지 로드 오류:", err));
  }, [subject]);
      
  const handleInputChange = (index, value) => {
    setImages((prev) =>
      prev.map((img, i) =>
        i === index ? { ...img, answer: value } : img
      )
    );
  };
  console.log("제출 직전 images 배열:", images);

  const handleSubmit = () => {
  const payload = {
    subject,
    studentAnswersList: images
      .filter((img) => {
        const qNum = Number(img.questionNumber);
        const hasAnswer = img.answer && img.answer.trim() !== "";
        return !isNaN(qNum) && hasAnswer;
      })
      .map((img) => ({
        student_id: String(img.student_id),
        answers: [
          {
            question_number: Number(img.questionNumber),
            sub_question_number: img.subQuestionNumber != null ? Number(img.subQuestionNumber) : null,
            student_answer: img.answer.trim(),
          },
        ],
      })),
  };
  console.log("백엔드로 전송하는 payload (JSON):\n", JSON.stringify(payload, null, 2));
  axios
    .put("/responses", payload, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    })
    .then(() => {
      navigate("/past-results", { state: { subject } });
    })
    .catch((err) => console.error("제출 오류:", err));
};

  return (
    <div className="bg-white flex flex-row justify-center w-full min-h-screen">
      <div className="bg-white w-full max-w-[1440px] h-[900px] relative">
        {/* 로그아웃 버튼 */}
        <div className="absolute top-[29px] right-[35px]">
            <Button
                variant="link"
                className="font-normal text-xl text-black"
                onClick={() => {
                const confirmLogout = window.confirm("로그아웃하시겠습니까?");
                if (confirmLogout) {
                    // 🔐 로그인 유지용 토큰 삭제
                    localStorage.removeItem("token");

                    // ✉️ 쿠키 기반이면 쿠키도 삭제 필요 (예시)
                    // document.cookie = "your_cookie_name=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";

                    // 🔄 로그인 페이지로 이동
                    navigate("/");
                }
                }}
            >
                Logout
            </Button>
        </div>
    
        {/* 작은 로고 */}
        <button className="absolute w-32 h-[30px] top-[29px] left-[52px]"
        onClick={() => navigate("/main")}>
          <img
            src="/Checkmate5.png"
            alt="CheckMate Logo"
            className="w-full h-full object-cover"
          />
        </button>

        <div className="max-w-4xl mx-auto p-6">
          <h1 className="text-2xl font-bold mb-2">인식률 낮은 답안 확인</h1>
          <p className="text-lg text-gray-700 mb-6">
            <strong>시험 날짜:</strong> {examDate} <br />
            <strong>과목명:</strong> {subject}
          </p>
        </div>
        <div className="max-w-4xl mx-auto p-6 space-y-8">
          {images.map((img, index) => (
            <div
              key={img.filename}
              className="flex flex-row items-center justify-start gap-6 border rounded-lg p-4 shadow-sm w-full bg-white"
              style={{ width: '100%', maxWidth: '800px', minHeight: '200px' }}
            >
              <div
                style={{
                  width: '200px',
                  height: '200px',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  border: '1px solid #ccc',
                }}
              >
                <img
                  src={`data:image/png;base64,${img.base64Data}`}
                  alt={`image-${index}`}
                  style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                />
              </div>

              <div style={{ flexGrow: 1 }}>
                <input
                  type="text"
                  value={img.answer}
                  onChange={(e) => handleInputChange(index, e.target.value)}
                  placeholder="이미지에 쓰여 있는 답을 입력해주세요"
                  className="w-full border rounded px-3 py-2"
                />
              </div>
            </div>
          ))}
          {images.length > 0 && (
            <div className="text-center">
              <Button className="bg-[#c7aee7] hover:bg-[#b79dd6] text-white text-xl px-4 py-2 rounded"
              onClick={handleSubmit}>제출하기</Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReviewLowConfidenceAnswers;


