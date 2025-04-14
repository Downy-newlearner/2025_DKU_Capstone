import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Input } from "./ui/input";
import { Separator } from "./ui/separator";
import { Calendar } from "lucide-react";
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const Grading = () => {
    const navigate = useNavigate();
    const [examDate, setExamDate] = useState("");
    const [subject, setSubject] = useState("");
    const [answers, setAnswers] = useState([
        { text: "", type: "객관식" }
    ]);
    const [answerFields, setAnswerFields] = useState([{ number: 1, label: "Enter the answer" }]);
    
    const addAnswerField = () => {
        const nextNumber = answerFields.length + 1;
        setAnswerFields([...answerFields, { number: nextNumber, label: "Enter the answer" }]);
    };

    // const handleSubmit = async () => {
    //     try {
    //         const response = await api.post("/api/submit-grading", {
    //             examDate,
    //             subject,
    //             answers
    //         });

    //         if (response.status === 200) {
    //             alert("제출 완료!");
    //         }
    //     } catch (error) {
    //         console.error("제출 실패:", error);
    //         alert("오류 발생");
    //     }
    // };
    const handleSubmit = () => {
        console.log("제출된 데이터:", answers);
        // 여기서 실제로 백엔드로 POST 요청을 보내거나 다음 페이지로 이동 등 처리를 넣으면 돼
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
    
            {/* Instruction text */}
            <div className="top-[220px] left-9 font-normal text-black text-xl absolute text-center tracking-[0] leading-[normal] font-['Poppins-Regular','Helvetica']">
            * 채점을 위한 정보를 입력해주세요.
            </div>

            {/* Left side form card */}
            <Card className="absolute w-[390px] h-[345px] top-[285px] left-9 rounded-[10px] border border-solid border-black shadow-[0px_4px_4px_#00000040]">
                <CardContent className="pt-10 px-4 relative">
                    
                    {/* 시험 날짜 라벨 */}
                    <div className="mb-2">
                    <div className="inline-block px-4 py-2 bg-[#FFF9C4] rounded-full font-bold text-black text-2xl">
                        시험 날짜
                    </div>
                    </div>

                    {/* 날짜 입력 필드 */}
                    <input
                    type="date"
                    value={examDate}
                    onChange={(e) => setExamDate(e.target.value)}
                    className="w-[90%] mb-6 px-4 py-2 rounded bg-[#fef1f1] border border-gray-300 text-lg ml-2"
                    />

                    {/* 과목명 라벨 */}
                    <div className="pt-6 mb-2">
                    <div className="inline-block px-4 py-2 bg-[#FFF9C4] rounded-full font-bold text-black text-2xl">
                        과목명
                    </div>
                    </div>

                    {/* 과목명 입력 필드 */}
                    <div className="relative w-full">
                        <Input
                        className="w-full text-[20px] placeholder:text-gray-400 border-none rounded-none focus-visible:ring-0 font-['Poppins-Regular','Helvetica']"
                        placeholder="Enter your subject name"
                        value={subject}
                        onChange={(e) => setSubject(e.target.value)}
                        />
                        <Separator className="absolute bottom-1 bg-black h-[2px] w-[90%] ml-2" />
                    </div>
                </CardContent>
                </Card>


            {/* Answer fields section */}
            <div className="absolute left-[575px] top-[284px]">
            {answers.map((answer, index) => (
                <div key={index} className="flex items-center mb-6">
                {/* 번호 */}
                <span className="text-3xl font-bold mr-4 w-8">{index + 1}.</span>

                {/* 입력창 + 밑줄 */}
                <div className="w-[500px] border-b-2 border-black">
                    <input
                    type="text"
                    placeholder="Enter the answer"
                    value={answers[index].text}
                    onChange={(e) => {
                        const updated = [...answers];
                        updated[index] = e.target.value;
                        setAnswers(updated);
                    }}
                    className="w-full text-xl placeholder-gray-400 bg-transparent focus:outline-none"
                    />
                </div>

                {/* 드롭다운 */}
                <select
                    value={answer.type}
                    onChange={(e) => {
                        const updated = [...answers];
                        updated[index].type = e.target.value;
                        setAnswers(updated);
                    }}
                    className="ml-4 px-4 py-2 border rounded text-lg"
                    >
                    <option value="객관식">객관식</option>
                    <option value="주관식">주관식</option>
                    <option value="단답형">단답형</option>
                    <option value="ox">OX</option>
                </select>

                {/* 체크박스 (객관식 or 단답형일 때만) */}
                {(answer.type === "객관식" || answer.type === "단답형") && (
                <label className="ml-4 flex items-center space-x-2 text-sm">
                    <input
                    type="checkbox"
                    checked={answer.multiple}
                    onChange={(e) => {
                        const updated = [...answers];
                        updated[index].multiple = e.target.checked;
                        setAnswers(updated);
                    }}
                    />
                    <span>답 2개 이상</span>
                </label>
                )}
            </div>
            ))}

            <div className="flex gap-4 mt-6">
                {/* 번호 추가하기 버튼 */}
                <Button
                    onClick={() => setAnswers([...answers,{ text: "", type: "객관식" }])}
                    className="bg-[#c7aee7] rounded-[5px] hover:bg-[#b79dd6] text-white text-xl px-6 py-2 font-['Poppins-Medium','Helvetica']"
                >
                    번호 추가하기
                </Button>

                {/* 번호 삭제하기 버튼 */}
                <Button
                    onClick={() => {
                    if (answers.length > 1) {
                        setAnswers(answers.slice(0, -1)); // 마지막 항목 제거
                    } else {
                        alert("최소 1개의 번호는 있어야 합니다!");
                    }
                    }}
                    className="bg-[#e7aeca] rounded-[5px] hover:bg-[#d69dba] text-white text-xl px-6 py-2 font-['Poppins-Medium','Helvetica']"
                >
                    번호 삭제하기
                </Button>
                
                {/* Submit button */}
                <Button
                    onClick={handleSubmit}
                    className="bg-[#a2c7e7] text-white px-4 py-2 rounded hover:bg-[#8db9de] text-xl font-['Poppins-Medium','Helvetica'] ml-[350px]"
                    >
                    제출
                </Button>
            </div>
        </div>
        </div>
        </div>
    );
};

export default Grading;
