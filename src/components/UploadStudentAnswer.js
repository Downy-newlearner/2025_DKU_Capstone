import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import axios from "../api/axios";

const UploadStudentAnswer = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [zipFile, setZipFile] = useState(null);
  const [xlsxFile, setXlsxFile] = useState(null);

  const handleUpload = () => {
    if (!zipFile || !xlsxFile) {
      alert("두 파일 모두 선택해주세요.");
      return;
    }

    const formData = new FormData();
    formData.append("subject", state.subject); 
    formData.append("answerSheetZip", zipFile);
    formData.append("attendanceSheet", xlsxFile);

    axios
      .post("/responses/upload-answer", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })
      .then(() => {
        navigate("/student-id-pending", {
          state: { subject: state.subject }, 
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
          <img
            src="/Checkmate5.png"
            alt="CheckMate Logo"
            className="w-full h-full object-cover"
          />
        </button>
        <div className="absolute w-[383px] h-[90px] top-[38px] left-[532px]">
          <img
            src="/Checkmate5.png"
            alt="CheckMate"
            className="w-full h-full object-cover mb-2"
          />
          <img src="/Vector 9.png" alt="밑줄" className="w-[400px] object-contain" />
        </div>

        <h2 className="absolute top-[260px] left-1/2 transform -translate-x-1/2 text-2xl font-semibold text-black">
          📄 학생 답안과 출석부를 업로드하세요
        </h2>

        <div className="absolute top-[330px] left-1/2 transform -translate-x-1/2 bg-white rounded-2xl shadow-lg p-8 w-full max-w-md text-center space-y-6">
          {/* ZIP 파일 업로드 */}
          <div>
            <label className="block font-medium text-gray-700 mb-1">학생 답안 ZIP 파일</label>
            <input
              type="file"
              accept=".zip"
              onChange={(e) => setZipFile(e.target.files[0])}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full
                file:border-0 file:text-sm file:font-semibold
                file:bg-purple-50 file:text-purple-700
                hover:file:bg-purple-100"
            />
            <p className="text-gray-600 mt-1">
              {zipFile ? `선택된 파일: ${zipFile.name}` : "선택된 파일 없음"}
            </p>
          </div>

          {/* XLSX 파일 업로드 */}
          <div>
            <label className="block font-medium text-gray-700 mb-1">출석부 (.xlsx)</label>
            <input
              type="file"
              accept=".xlsx"
              onChange={(e) => setXlsxFile(e.target.files[0])}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full
                file:border-0 file:text-sm file:font-semibold
                file:bg-purple-50 file:text-purple-700
                hover:file:bg-purple-100"
            />
            <p className="text-gray-600 mt-1">
              {xlsxFile ? `선택된 파일: ${xlsxFile.name}` : "선택된 파일 없음"}
            </p>
          </div>

          <Button
            onClick={handleUpload}
            className="bg-[#c7aee7] hover:bg-[#b79dd6] text-white text-lg w-full py-2 rounded-xl"
          >
            업로드 및 제출
          </Button>
        </div>
      </div>
    </div>
  );
};

export default UploadStudentAnswer;
