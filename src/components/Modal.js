import React from "react";
import { useNavigate } from "react-router-dom"; // 페이지 이동을 위한 Hook

export const Modal = ({ openModal, setOpenModal }) => {
  const navigate = useNavigate(); // useNavigate 훅 사용
  if (!openModal) return null; // ✅ openModal이 false면 렌더링하지 않음
  

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
      <div className="bg-white p-6 rounded-lg shadow-lg w-[451px]">
        <h2 className="text-2xl font-medium text-center mb-6">로그아웃 하시겠습니까?</h2>
        <div className="flex justify-between mt-6">
          <button
            className="w-[124px] h-[51px] bg-gray-300 hover:bg-gray-400 rounded-md"
            onClick={() => {
              setOpenModal(false); // 클릭 이벤트로 모달창 닫히게 하기
              navigate("/main");
            }}
          >
            취소
          </button>
          {!openModal ? setOpenModal(true) : null} 
          <button
            className="w-[124px] h-[51px] bg-gray-300 hover:bg-gray-400 rounded-md"
            onClick={() => {
              setOpenModal(false);
              navigate("/");
            }}
          >
            확인
          </button>
        </div>
      </div>
    </div>
  );
};

export default Modal;
