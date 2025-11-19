import React, { useEffect, useState } from "react";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Separator } from "./ui/separator";
import { useNavigate } from "react-router-dom";
import config from "../config";

export const Mypage = () => {
    const navigate = useNavigate();
    const [userData, setUserData] = useState({
        email: "",
        username: "",
    });

  {/* 로그인된 사용자 정보 불러오기 (예: JWT 토큰을 통해 인증) */}
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const res = await fetch(`${config.api.baseURL}/user`, {
          method: "GET",
          credentials: "include", // 쿠키 기반 인증
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        });

        if (!res.ok) throw new Error("사용자 정보를 불러오는데 실패했습니다.");

        const data = await res.json();
        setUserData({
          email: data.email,
          username: data.name,
        });
      } catch (error) {
        console.error("유저 데이터 에러:", error.message);
        alert("사용자 정보를 불러올 수 없습니다. 다시 로그인해주세요.");
        navigate("/"); // 실패 시 로그인 페이지로 이동
      }
    };

    fetchUserData();
  }, [navigate]);

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

        {/* 계정정보 타이틀 */}
        <div className="absolute w-[136px] h-[45px] top-[220px] left-[47px] bg-[#FFF9C4] rounded-full flex items-center justify-center">
          <h2 className="font-bold text-3xl text-black">계정정보</h2>
        </div>

        {/* 사용자 정보 카드 */}
        <Card className="absolute w-[390px] h-[329px] top-[337px] left-[42px] rounded-[10px] border border-solid border-black shadow-[0px_4px_4px_#00000040]">
          <CardContent className="pt-[54px] px-6">
            <div className="relative">
              {/* Email */}
              <div className="mb-10">
                <div className="inline-block bg-[#f4dede] px-3 rounded-full [-webkit-text-stroke:1px_#000000] -ml-1">
                    <span className="font-normal text-[22px]">Email</span>
                </div>
                <div className="mt-2 font-normal text-xl">{userData.email}</div>
                <Separator className="mt-2 h-0.5 bg-black" />
              </div>

              {/* User Name */}
              <div className="mt-[53px]">
                <div className="inline-block bg-[#f4dede] px-3.5 rounded-full [-webkit-text-stroke:1px_#000000] -ml-1">
                  <span className="font-normal text-[22px]">User Name</span>
                </div>
                <div className="mt-2 font-normal text-xl">{userData.username}</div>
                <Separator className="mt-2 h-0.5 bg-black" />
              </div>
            </div>
          </CardContent> 
        </Card>

        {/* Password Change Message */}
        <div className="absolute top-[701px] left-[49px] font-normal text-black text-xl text-center">
            *비밀번호 변경을 원하신다면 하단의 버튼을 눌러주세요.
        </div>

        {/* Decorative Elements */}
        <div className="absolute w-[798px] h-[601px] top-[141px] right-[90px]">
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


        {/* 비밀번호 변경 버튼 */}
        <div className="absolute w-[330px] h-14 top-[810px] left-[560px]">
          <Button className="w-[278px] h-14 bg-[#c7aee7] hover:bg-[#b79ad3] rounded-[5px] text-3xl font-medium text-white"
          onClick={() => navigate("/changepassword")}>
            비밀번호 변경하기
          </Button>
        </div>
      </div>
    </div>
  );
}

export default Mypage;