import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "../api/axios";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Download } from "lucide-react";

const GradingResults = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const subject = state?.subject;

  const [zipList, setZipList] = useState([]);

  useEffect(() => {
    if (!subject) return;

    axios
      .get(`/exams/student-zip-list?subject=${encodeURIComponent(subject)}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })
      .then((res) => setZipList(res.data))
      .catch((err) => {
        console.error("ZIP 목록 불러오기 실패", err);
        alert("파일 목록을 불러오는 데 실패했습니다.");
      });
  }, [subject]);

  const handleDownload = async (url, fileName) => {
    try {
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        responseType: "blob",
      });

      const blob = new Blob([response.data], { type: "application/zip" });
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = fileName;
      link.click();
      window.URL.revokeObjectURL(link.href);
    } catch (err) {
      console.error("다운로드 실패", err);
    }
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
                <div className="bg-white min-h-screen p-20">
                  <h1 className="text-3xl font-bold mb-6">📦 {subject} 채점 결과 ZIP 파일</h1>

                  {zipList.length === 0 ? (
                    <p className="text-gray-500">ZIP 파일이 없습니다.</p>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {zipList.map((item, idx) => (
                        <Card key={idx} className="flex justify-between items-center p-4">
                          <CardContent className="flex justify-between items-center w-full px-0">
                            <span className="text-md font-medium">{item.fileName}</span>
                            <Button
                              variant="ghost"
                              onClick={() => handleDownload(item.downloadUrl, item.fileName)}
                              className="text-indigo-600 hover:text-indigo-800"
                            >
                              <Download className="w-5 h-5" />
                            </Button>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
  );
};

export default GradingResults;
