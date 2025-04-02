import React from "react";
import { Card, CardContent } from "./ui/card";
import { useState } from "react";
import { Button } from "./ui/button";
import { useNavigate } from "react-router-dom";
import Modal from "./Modal";
import "./main.css";

const Main = () => {
  const navigate = useNavigate();
  const [openModal, setOpenModal] = useState(false);

  return (
    <div className="flex justify-center w-full min-h-screen bg-white">
      <Modal openModal={openModal} setOpenModal={setOpenModal} />
      <div className="relative w-full max-w-[1440px] h-[900px]">
        {/* Header Section */}
        <header className="absolute w-full h-[253px] top-0 left-0">
          {/* Navigation */}
          <nav className="flex justify-end items-center p-4 space-x-4">
            <button
              className="font-['Poppins-Regular'] text-xl"
              onClick={() => {
                setOpenModal(true);
              }}
            >
              Logout
            </button>
            <div className="border-l border-black h-6"></div>
            <div className="font-['Poppins-Regular'] text-xl">Mypage</div>
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
                <Button className="w-[180px] h-[60px] bg-[#c2afe8] text-white text-2xl rounded-md hover:bg-[#b399e0]">
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
                <Button className="w-[300px] h-[60px] bg-[#c2afe8] text-white text-2xl rounded-md hover:bg-[#b399e0]">
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
