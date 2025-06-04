import React, { useEffect, useState } from "react";
import axios from "../api/axios";
import { Button } from "./ui/button";
import { Download } from "lucide-react";
import { Card, CardContent } from "./ui/card";
import { useNavigate } from "react-router-dom";

const PastResultsPage = () => {
  const navigate = useNavigate();
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [zipList, setZipList] = useState([]); // ✅ 타입 제거

  useEffect(() => {
    axios
      .get("/exams", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })
      .then((res) => setSubjects(res.data))
      .catch((err) => console.error("과목 불러오기 실패", err));
  }, []);

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
            <div className="p-20">
              <h1 className="text-3xl font-bold mb-6">📁 채점한 과목 목록</h1>

              <div className="mb-8 flex flex-col gap-2">
                {subjects.map((subjectObj) => (
                  <Button
                    key={subjectObj.id}
                    className={`${
                      selectedSubject === subjectObj.subject 
                      ? "bg-gray-300 text-black" 
                      : "bg-gray-100 hover:bg-gray-200 text-black"
                    } text-left px-5 py-2 rounded`}
                    onDoubleClick={() => navigate("/subject-zip-list", { state: { subject: subjectObj.subject } })}
                  >
                    {subjectObj.subject}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </div>
  );
};

export default PastResultsPage;
