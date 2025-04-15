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
        { text: "", type: "객관식", multiple: false, tailQuestions: [] }
    ]);

    const handleSubmit = () => {
        const dataToSubmit = {
            examDate,
            subject,
            answers,
        };
        console.log("제출된 데이터:", dataToSubmit);
    };

    const addTailQuestion = (index) => {
        const updated = [...answers];
        if (!updated[index].tailQuestions) updated[index].tailQuestions = [];
        updated[index].tailQuestions.push({ text: "", multiple: false });
        setAnswers(updated);
    };

    const removeTailQuestion = (index) => {
        const updated = [...answers];
        if (updated[index].tailQuestions && updated[index].tailQuestions.length > 0) {
            updated[index].tailQuestions.pop();
            setAnswers(updated);
        }
    };

    const addAnswerField = () => {
        setAnswers([...answers, { text: "", type: "객관식", multiple: false, tailQuestions: [] }]);
    };

    const removeAnswerField = () => {
        if (answers.length > 1) {
            setAnswers(answers.slice(0, -1));
        } else {
            alert("최소 1개의 번호는 있어야 합니다!");
        }
    };

    return (
        <div className="bg-white flex flex-row justify-center w-full min-h-screen">
            <div className="bg-white w-full max-w-[1440px] h-[900px] relative">
                <div className="absolute top-[29px] right-[35px]">
                    <Button
                        variant="link"
                        className="font-normal text-xl text-black"
                        onClick={() => {
                            const confirmLogout = window.confirm("로그아웃하시겠습니까?");
                            if (confirmLogout) {
                                localStorage.removeItem("token");
                                navigate("/");
                            }
                        }}
                    >
                        Logout
                    </Button>
                </div>

                <button className="absolute w-32 h-[30px] top-[29px] left-[52px]" onClick={() => navigate("/main")}> 
                    <img src="/Checkmate5.png" alt="CheckMate Logo" className="w-full h-full object-cover" />
                </button>

                <div className="absolute w-[383px] h-[90px] top-[38px] left-[532px]">
                    <img src="/Checkmate5.png" alt="CheckMate" className="w-full h-full object-cover mb-2" />
                    <img src="/Vector 9.png" alt="밑줄" className="w-[400px] object-contain" />
                </div>

                <div className="top-[220px] left-9 font-normal text-black text-xl absolute text-center tracking-[0] leading-[normal] font-['Poppins-Regular','Helvetica']">
                    * 채점을 위한 정보를 입력해주세요.
                </div>

                <Card className="absolute w-[390px] h-[345px] top-[285px] left-9 rounded-[10px] border border-solid border-black shadow-[0px_4px_4px_#00000040]">
                    <CardContent className="pt-10 px-4 relative">
                        <div className="mb-2">
                            <div className="inline-block px-4 py-2 bg-[#FFF9C4] rounded-full font-bold text-black text-2xl">
                                시험 날짜
                            </div>
                        </div>
                        <input
                            type="date"
                            value={examDate}
                            onChange={(e) => setExamDate(e.target.value)}
                            className="w-[90%] mb-6 px-4 py-2 rounded bg-[#fef1f1] border border-gray-300 text-lg ml-2"
                        />
                        <div className="pt-6 mb-2">
                            <div className="inline-block px-4 py-2 bg-[#FFF9C4] rounded-full font-bold text-black text-2xl">
                                과목명
                            </div>
                        </div>
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

                <div className="absolute left-[575px] top-[284px]">
                    {answers.map((answer, index) => (
                        <div key={index} className="mb-6">
                            <div className="flex items-center mb-2">
                                <span className="text-3xl font-bold mr-4 w-8">{index + 1}.</span>
                                <div className="w-[500px] border-b-2 border-black">
                                    <input
                                        type="text"
                                        placeholder="Enter the answer"
                                        value={answer.text}
                                        onChange={(e) => {
                                            const updated = [...answers];
                                            updated[index].text = e.target.value;
                                            setAnswers(updated);
                                        }}
                                        className="w-full text-xl placeholder-gray-400 bg-transparent focus:outline-none"
                                    />
                                </div>
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

                            <div className="ml-10 flex flex-col items-start">
                                {answer.tailQuestions.map((q, idx) => (
                                    <div key={idx} className="flex items-center mb-2">
                                        <span className="text-lg font-semibold mr-2">({idx + 1})</span>
                                        <input
                                            type="text"
                                            value={q.text}
                                            onChange={(e) => {
                                                const updated = [...answers];
                                                updated[index].tailQuestions[idx].text = e.target.value;
                                                setAnswers(updated);
                                            }}
                                            className="w-[400px] border-b-2 border-black text-lg bg-transparent focus:outline-none mr-2"
                                            placeholder="Enter the answer"
                                        />
                                        <label className="flex items-center space-x-2 text-sm">
                                            <input
                                                type="checkbox"
                                                checked={q.multiple}
                                                onChange={(e) => {
                                                    const updated = [...answers];
                                                    updated[index].tailQuestions[idx].multiple = e.target.checked;
                                                    setAnswers(updated);
                                                }}
                                            />
                                            <span>답 2개 이상</span>
                                        </label>
                                    </div>
                                ))}

                                <div className="flex gap-2 mt-2">
                                    <Button
                                        onClick={() => addTailQuestion(index)}
                                        className="bg-[#c7c7f0] rounded-[5px] hover:bg-[#b5b5e0] text-white text-sm px-4 py-1 font-['Poppins-Medium','Helvetica']"
                                    >
                                        꼬리문제 추가
                                    </Button>
                                    <Button
                                        onClick={() => removeTailQuestion(index)}
                                        className="bg-[#f2bcbc] rounded-[5px] hover:bg-[#e1a9a9] text-white text-sm px-4 py-1 font-['Poppins-Medium','Helvetica']"
                                    >
                                        꼬리문제 삭제
                                    </Button>
                                </div>
                            </div>
                        </div>
                    ))}

                    <div className="flex gap-4 mt-6">
                        <Button
                            onClick={addAnswerField}
                            className="bg-[#c7aee7] rounded-[5px] hover:bg-[#b79dd6] text-white text-xl px-4 py-2 font-['Poppins-Medium','Helvetica']"
                        >
                            번호 추가
                        </Button>

                        <Button
                            onClick={removeAnswerField}
                            className="bg-[#e7aeca] rounded-[5px] hover:bg-[#d69dba] text-white text-xl px-4 py-2 font-['Poppins-Medium','Helvetica']"
                        >
                            번호 삭제
                        </Button>

                        <Button
                            onClick={handleSubmit}
                            className="bg-[#a2c7e7] text-white px-4 py-2 rounded hover:bg-[#8db9de] text-xl font-['Poppins-Medium','Helvetica'] ml-[450px]"
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
