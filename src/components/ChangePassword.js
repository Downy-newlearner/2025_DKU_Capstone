import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Input } from "./ui/input";
import { EyeIcon, EyeOffIcon } from "lucide-react";
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const ChangePassword = () => {
  const navigate = useNavigate();
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      alert("모든 비밀번호를 입력해주세요.");
      return;
    }

    if (newPassword !== confirmPassword) {
      alert("새 비밀번호와 확인 비밀번호가 일치하지 않습니다.");
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const response = await fetch("http://13.209.197.61:8080/change-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      if (response.ok) {
        alert("비밀번호가 성공적으로 변경되었습니다.");
        navigate("/main");
      } else {
        const errorData = await response.json();
        alert(`변경 실패: ${errorData.message || "알 수 없는 오류"}`);
      }
    } catch (error) {
      console.error(error);
      alert("서버 오류가 발생했습니다.");
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

        {/* 폼 카드 */}
        <Card className="absolute w-[505px] h-[470px] top-[310px] left-[42px] rounded-[10px] border-[0.5px] border-solid border-[#868686] shadow-lg">
          <CardContent className="p-8 space-y-6">

            {/* Current Password */}
            <div className="space-y-2">
              <div className="text-black text-base mb-2">Current Password</div>
              <div className="relative">
                <Input
                  type={showCurrentPassword ? "text" : "password"}
                  placeholder="Enter your Password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="h-[59px] pl-6 text-sm font-light"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  className="absolute right-4 top-1/2 transform -translate-y-1/2"
                >
                  {showCurrentPassword ? <EyeOffIcon size={20} /> : <EyeIcon size={20} />}
                </button>
              </div>
            </div>

            {/* New Password */}
            <div className="space-y-2">
              <div className="text-black text-base mb-2">New Password</div>
              <div className="relative">
                <Input
                  type={showNewPassword ? "text" : "password"}
                  placeholder="Enter new Password"
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
              onClick={handleChangePassword}
              className="mt-[79px] h-[57px] w-full bg-[#c7aee7] text-white rounded-md hover:bg-[#c7aee7]/90 text-base font-medium"
            >
              Register
            </Button>

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
  );
};

export default ChangePassword;
