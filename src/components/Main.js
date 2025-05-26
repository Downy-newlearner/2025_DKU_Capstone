import React from "react";
import { Card, CardContent } from "./ui/card";
import { useState } from "react";
import { Button } from "./ui/button";
import { useNavigate } from "react-router-dom";
import "./main.css";

const Main = () => {
  const navigate = useNavigate();

  return (
    <div className="flex justify-center w-full min-h-screen bg-white">
      <div className="relative w-full max-w-[1440px] h-[900px]">
        {/* Header Section */}
        <header className="absolute w-full h-[253px] top-0 left-0">
          {/* Navigation */}
          <nav className="flex justify-end items-center p-4 space-x-4">
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
            <div className="border-l border-black h-6"></div>
            <button className="font-['Poppins-Regular'] text-xl"
              onClick={() => {navigate("/mypage")}} // 클릭 시 mypage로 이동
              >
                Mypage
            </button>
          </nav>

          {/* Logo + Underline */}
          <div className="title-container flex flex-col items-center mt-8">
            <img
              src="/Checkmate5.png"
              alt="CheckMate 로고"
              className="w-[300px] object-contain mb-2"
            />
            <img
              src="/Vector 6.png"
              alt="밑줄"
              className="w-[280px] object-contain"
            />
          </div>
        </header>

        {/* 메인 카드 섹션 */}
        <main className="absolute top-[350px] w-full flex justify-center gap-32">
          {/* Grading Section */}
          <div className="flex flex-col items-start w-[460px]">
            <div className="bg-[#fff9c4] text-black font-semibold text-xl px-4 py-2 rounded-full mb-2">
              Grading
            </div>
            <Card className="rounded-xl border-gray-400 shadow-md w-full">
              <CardContent className="py-8 px-6 flex flex-col items-center">
                <p className="text-xl mb-6 text-center">시험지 채점이 필요하다면?</p>
                <Button className="w-[180px] h-[60px] bg-[#c2afe8] text-white text-2xl rounded-md hover:bg-[#b399e0]"
                onClick={() => navigate("/grading")}>
                  채점하기
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Check Section */}
          <div className="flex flex-col items-start w-[460px]">
            <div className="bg-[#fff9c4] text-black font-semibold text-xl px-4 py-2 rounded-full mb-2">
              Check
            </div>
            <Card className="rounded-xl border-gray-400 shadow-md w-full">
              <CardContent className="py-8 px-6 flex flex-col items-center">
                <p className="text-xl mb-6 text-center">이전 시험 결과를 학생별로 확인하고 싶다면?</p>
                <Button className="w-[300px] h-[60px] bg-[#c2afe8] text-white text-2xl rounded-md hover:bg-[#b399e0]"
                onClick={() => navigate("/past-results")}>
                  이전 채점 결과 확인하기
                </Button>
              </CardContent>
            </Card>
          </div>

        </main>
      </div>
    </div>
  );
};

export default Main;
