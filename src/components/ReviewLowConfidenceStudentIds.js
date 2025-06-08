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
  const examDate = state?.examDate || null;
  
  

  useEffect(() => {
    if (!subject) return;

    axios
      .get(`/student/${encodeURIComponent(subject)}/images`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })
      .then((res) => {
        const images = res.data?.lowConfidenceImages ?? [];
        const prepared = images.map((item) => ({
          fileName: item.file_name,
          base64Data: item.base64_data,
          confirmedId: "",
        }));
        setEntries(prepared);
      })
      .catch((err) => {
        console.error("신뢰도 낮은 학번 이미지 불러오기 실패", err);
      });
  }, [navigate, subject, examDate]);

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
      student_list: entries.map(({ fileName, confirmedId, base64Data }) => ({
        student_id: confirmedId,
        file_name: fileName,
        base64_data: base64Data, // ✅ base64를 배열로 감싸기
      })),
    };
    console.log("전송 데이터:", JSON.stringify(payload, null, 2));
    axios
      .post("/student/update-id", payload, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
      })
      .then(() => {
        navigate("/grading-pending", {
          state: {
          subject,
          examDate: state?.examDate || null,
          },
        });
      })
  
      .catch((err) => {
        console.error("학번 보정 제출 실패", err);
        alert("제출 중 오류가 발생했습니다.");
      });

      
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
                        src={`data:image/jpeg;base64,${entry.base64Data}`}
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
                  className="mt-10 bg-[#c7aee7] hover:bg-[#b79dd6] text-white text-xl px-4 py-2 rounded"
                  onClick={handleSubmit}
                >
                  제출하기
                </Button>
              )}
            </div>
          </div>
        </div>
  );
};

export default ReviewLowConfidenceStudentIds;
