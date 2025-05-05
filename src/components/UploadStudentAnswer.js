import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import axios from "../api/axios";

const UploadStudentAnswer = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [file, setFile] = useState(null);

  const handleUpload = () => {
    if (!file) {
      alert("파일을 선택해주세요.");
      return;
    }

    const formData = new FormData();
    formData.append("examId", state.examId);
    formData.append("answerSheet", file);

    axios.post("/exams/upload-answer", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      })
      .then(() => {
        navigate("/grading-pending",{
          state: { examId: state.examId },
      });
    })
    .catch(() => alert("업로드 중 오류 발생"));
  };

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
            <div className="p-20">
                <h1 className="text-2xl font-bold mb-4">학생 답안지를 업로드하세요</h1>
                <input type="file" onChange={(e) => setFile(e.target.files[0])} />
                <Button onClick={handleUpload} className="mt-4">업로드 및 제출</Button>
            </div>
        </div>
    </div>
  );
};

export default UploadStudentAnswer;
