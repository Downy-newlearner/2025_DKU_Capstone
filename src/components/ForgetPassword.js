import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Input } from "./ui/input";

const ForgetPassword = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");

  const handleSendResetEmail = async () => {
    if (!email) {
        alert("이메일을 입력해주세요.");
        return;
      }
    
      try {
        const response = await fetch("http://13.209.197.61:8080/reset-request", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: email, // 사용자가 입력한 이메일을 보내기
          }),
        });
    
        if (response.ok) {
          alert("비밀번호 재설정 링크가 이메일로 전송되었습니다!");
          navigate("/"); // 메인 페이지로 이동
        } else {
          const errorData = await response.json();
          alert(`전송 실패: ${errorData.message || "알 수 없는 오류"}`);
        }
      } catch (error) {
        console.error("에러 발생:", error);
        alert("서버 오류가 발생했습니다.");
      }
  };

  return (
    <div className="bg-white flex flex-row justify-center w-full min-h-screen">
      <div className="w-full max-w-[1440px] relative py-[30px] px-[42px]">
        {/* 작은 로고 */}
        <div className="w-[120px] h-auto">
          <img src="/Checkmate5.png" alt="Logo" className="object-contain w-full" />
        </div>

        <div className="flex flex-row mt-[80px] px-[69px]">
          {/* 왼쪽 카드 */}
          <div className="mt-[30px]">
            <Card className="h-[500px] w-[505px] rounded-[10px] border-[0.5px] border-solid border-[#868686] shadow-lg">
                <CardContent className="p-[35px]">
                <div className="font-bold text-black text-[31px] mb-3">
                    Forget Password?
                </div>
                <div className="text-black text-base mb-8">
                    CheckMate
                </div>

                {/* Email 입력 */}
                <div className="space-y-2">
                    <div className="text-black text-base mb-2">
                    Email
                    </div>
                    <Input
                    name="email"
                    className="h-[59px] text-sm font-light"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    />
                </div>

                {/* 안내 문구 */}
                <div className="mt-8 text-sm text-gray-600 leading-relaxed">
                    If you forget your password, just write and authenticate your email address!!<br />
                    We will send the link that you can reset your password!
                </div>

                {/* 버튼 */}
                <Button
                    className="mt-10 h-[57px] w-full bg-[#c7aee7] text-white rounded-md hover:bg-[#b99dd6] text-base font-medium"
                    onClick={handleSendResetEmail}
                >
                    Authenticate
                </Button>
                </CardContent>
            </Card>
          </div>

            {/* 오른쪽 이미지 */}
            <div className="flex-1 flex items-center justify-center ml-[60px]">
                <img
                className="w-[551px] h-[551px] object-contain"
                alt="Small team discussing ideas"
                src="/loginimage1.png"
                />
            </div>
        </div>
      </div>
    </div>
  );
};

export default ForgetPassword;
