import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom"; // useLocation 추가
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Input } from "./ui/input";
import { EyeIcon, EyeOffIcon } from "lucide-react";

const AuthenticatePassword = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [token, setToken] = useState("");
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // 링크에서 token 추출
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const tokenParam = params.get("token");
    if (tokenParam) {
      setToken(tokenParam);
    } else {
      alert("유효하지 않은 링크입니다.");
      navigate("/");
    }
  }, [location, navigate]);

  const handleResetPassword = async () => {
    if (!newPassword || !confirmPassword) {
      alert("모든 비밀번호를 입력해주세요.");
      return;
    }

    if (newPassword !== confirmPassword) {
      alert("비밀번호가 일치하지 않습니다.");
      return;
    }

    try {
      const response = await fetch("http://13.209.197.61:8080/reset-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token: token,               // ✅ 바디에 token 포함
          new_password: newPassword,  // ✅ 같이 전송
        }),
      });

      if (response.ok) {
        alert("비밀번호가 성공적으로 변경되었습니다!");
        navigate("/");
      } else {
        const errorText = await response.text();  // 텍스트로 에러 파싱
        console.error("에러 응답:", errorText);
        alert(`변경 실패: ${errorText}`);
      }
    } catch (error) {
      console.error("에러 발생:", error);
      alert("서버 오류가 발생했습니다.");
    }
  };

  return (
    <div className="bg-white flex flex-row justify-center w-full min-h-screen">
          <div className="bg-white w-full max-w-[1440px] h-[900px] relative">
        
            {/* 작은 로고 */}
            <button className="absolute w-32 h-[30px] top-[29px] left-[52px]">
              <img
                src="/Checkmate5.png"
                alt="CheckMate Logo"
                className="w-full h-full object-cover"
              />
            </button>
    
            {/* 큰 로고 */}
            <div className="absolute w-[383px] h-[90px] top-[38px] left-[532px]">
              <img
                src="/Checkmate5.png"
                alt="CheckMate"
                className="w-full h-full object-cover mb-2"
              />
              <img
                  src="/Vector 9.png"
                  alt="밑줄"
                  className="w-[400px] object-contain"
                />
            </div>

            {/* 비밀번호 변경하기 타이틀 */}
            <div className="absolute w-[280px] h-[45px] top-[220px] left-[47px] bg-[#FFF9C4] rounded-full flex items-center justify-center">
                <h2 className="font-bold text-3xl text-black">비밀번호 변경하기</h2>
            </div>

            <div className="flex flex-row mt-[80px] px-[69px]">
            {/* 왼쪽 카드 */}
            <div className="mt-[30px]">
                <Card className="absolute w-[505px] h-[350px] top-[310px] left-[42px] rounded-[10px] border-[0.5px] border-solid border-[#868686] shadow-lg">
                    <CardContent className="p-8 space-y-6">
                        <div className="space-y-6">
                        {/* New Password */}
                        <div className="space-y-2">
                            <div className="text-black text-base mb-2">New Password</div>
                            <div className="relative">
                            <Input
                                type={showNewPassword ? "text" : "password"}
                                placeholder="Enter your Password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                className="h-[59px] pl-6 text-sm font-light"
                            />
                            <button
                                type="button"
                                onClick={() => setShowNewPassword(!showNewPassword)}
                                className="absolute right-4 top-1/2 transform -translate-y-1/2"
                            >
                                {showNewPassword ? <EyeOffIcon size={20} /> : <EyeIcon size={20} />}
                            </button>
                            </div>
                        </div>

                        {/* Confirm Password */}
                        <div className="space-y-2">
                            <div className="text-black text-base mb-2">Confirm Password</div>
                            <div className="relative">
                            <Input
                                type={showConfirmPassword ? "text" : "password"}
                                placeholder="Confirm your Password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                className="h-[59px] pl-6 text-sm font-light"
                            />
                            <button
                                type="button"
                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                className="absolute right-4 top-1/2 transform -translate-y-1/2"
                            >
                                {showConfirmPassword ? <EyeOffIcon size={20} /> : <EyeIcon size={20} />}
                            </button>
                            </div>
                        </div>

                        {/* Submit */}
                        <Button
                            onClick={handleResetPassword}
                            className="mt-4 h-[57px] w-full bg-[#c7aee7] text-white rounded-md hover:bg-[#b99dd6] text-base font-medium"
                        >
                            Register
                        </Button>
                        </div>
                </CardContent>
                </Card>
            </div>

          {/* Decorative Elements */}
            <div className="absolute w-[798px] h-[601px] top-[141px] right-[45px]">
                {/* Pink blur circle (가장 뒤에) */}
                <div className="absolute w-[489px] h-[489px] top-9 right-0 bg-[#f8d3d3] rounded-full blur-[5px] opacity-50" />
                {/* White circle */}
                <div className="absolute w-[362px] h-[362px] top-[239px] left-4 bg-[#fdeded] blur-[5px] rounded-full opacity-50" />
                {/* Check 이미지 */}
                <img
                    src="/check.png"
                    alt="Check Image"
                    className="absolute w-[480px] h-[480px] top-[111px] left-[122px] object-cover"
                />          
            </div>
        </div>
      </div>
    </div>
  );
};

export default AuthenticatePassword;
