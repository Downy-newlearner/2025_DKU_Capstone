import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Input } from "./ui/input";
import { Separator } from "./ui/separator";
import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "../api/axios";

const Grading = () => {
  const location = useLocation();
  const { state } = useLocation();
  const examData = location.state;

  useEffect(() => {
    if (examData) {
      setExamDate(examData.exam_date?.split("T")[0] || "");
      setSubject(examData.subject || "");
      if (examData.questions) {
        // 문제 번호별로 메인과 꼬리문제를 그룹화
        const grouped = {};
        examData.questions.forEach((q) => {
          const num = q.question_number;
          if (!grouped[num]) {
            grouped[num] = [];
          }
          grouped[num].push(q);
        });
  
        const formatted = Object.values(grouped).map((questions) => {
          const main = questions.find((q) => q.sub_question_number === 0 || q.sub_question_number === null);
          const tails = questions.filter((q) => q.sub_question_number !== 0 && q.sub_question_number !== null);
          return {
            text: main?.answer || "",
            type: convertTypeReverse(main?.question_type || ""),
            multiple: main?.answer?.includes(",") || false,
            point: main?.point || 0,
            tailQuestions: tails.map((t) => ({
              text: t.answer,
              point: t.point,
              multiple: t.answer?.includes(",") || false,
            })),
          };
        });
  
        setAnswers(formatted);
      }
    }
  }, [examData]);
  const navigate = useNavigate();
  const [examDate, setExamDate] = useState("");
  const [subject, setSubject] = useState("");
  const [answers, setAnswers] = useState([
    { text: "", type: "객관식", multiple: false, point: 0, tailQuestions: [] },
  ]);

  const convertType = (type) => {
    switch (type) {
      case "객관식":
        return "multiple_choice";
      case "단답형":
        return "short_answer";
      case "주관식":
        return "descriptive";
      case "ox":
        return "TF";
      default:
        return "short_answer";
    }
  };

  const convertTypeReverse = (type) => {
    switch (type) {
      case "multiple_choice":
        return "객관식";
      case "short_answer":
        return "단답형";
      case "descriptive":
        return "주관식";
      case "TF":
        return "ox";
      default:
        return "단답형";
    }
  };
  
  const formatAnswer = (text, type) => {
    if (type === "ox") {
      if (text.trim() === "O") return "True";
      if (text.trim() === "X") return "False";
    }
    return text;
  };

  const handleSubmit = () => {
    if (!examDate) {
      alert("시험 날짜를 입력해주세요.");
      return;
    }
  
    const dateObj = new Date(examDate);
    if (isNaN(dateObj)) {
      alert("유효하지 않은 날짜입니다.");
      return;
    }
    console.log("현재 토큰:", localStorage.getItem("token"));
    const payload = {
      exam_date: new Date(examDate).toISOString().split("T")[0] + "T00:00:00",
      subject: subject,
      questions: [],
    };

    answers.forEach((answer, mainIndex) => {
      const hasTails = answer.tailQuestions.length > 0;

      if (!hasTails) {
        // 꼬리문제가 없을 때만 메인 문제 추가
        payload.questions.push({
          question_number: mainIndex + 1,
          sub_question_number: null,
          question_type: convertType(answer.type),
          answer: formatAnswer(answer.text, answer.type),
          point: answer.point,
        });
      } else {
        // 꼬리문제가 있을 경우, 메인 문제는 빼고 꼬리문제만 추가
        answer.tailQuestions.forEach((q, subIdx) => {
          payload.questions.push({
            question_number: mainIndex + 1,
            sub_question_number: subIdx + 1,
            question_type: convertType(answer.type),
            answer: formatAnswer(q.text, answer.type),
            point: q.point,
          });
        });
      }
    });

    console.log("제출 데이터:", payload);
    axios.post("/exams", payload, {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    })
    .then(res => {
      navigate("/grading-info", {
        state: res.data, // ✅ 서버에서 전체 exam DTO를 돌려준다면
      })
    })
    .catch((error) => {
      console.error("제출 실패:", error);
      alert("제출 중 오류가 발생했습니다.");
    });
  };

  const addAnswerField = () => {
    setAnswers([
      ...answers,
      { text: "", type: "객관식", multiple: false, point: 0, tailQuestions: [] },
    ]);
  };

  const removeAnswerField = () => {
    if (answers.length > 1) {
      setAnswers(answers.slice(0, -1));
    } else {
      alert("최소 1개의 번호는 있어야 합니다!");
    }
  };

  const addTailQuestion = (index) => {
    const updated = [...answers];
    updated[index].tailQuestions.push({ text: "", multiple: false, point: 0 });
    setAnswers(updated);
  };

  const removeTailQuestion = (index) => {
    const updated = [...answers];
    updated[index].tailQuestions.pop();
    setAnswers(updated);
  };

  return (
    <div className="bg-white flex flex-row justify-center w-full min-h-screen">
      <div className="bg-white w-full max-w-[1440px] h-[900px] relative">
        {/* 로그아웃 + 로고 */}
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
        <button
          className="absolute w-32 h-[30px] top-[29px] left-[52px]"
          onClick={() => navigate("/main")}
        >
          <img src="/Checkmate5.png" alt="CheckMate Logo" className="w-full h-full object-cover" />
        </button>
        <div className="absolute w-[383px] h-[90px] top-[38px] left-[532px]">
          <img src="/Checkmate5.png" alt="CheckMate" className="w-full h-full object-cover mb-2" />
          <img src="/Vector 9.png" alt="밑줄" className="w-[400px] object-contain" />
        </div>

        {/* 안내 문구 */}
        <div className="top-[220px] left-9 font-normal text-black text-xl absolute text-center">
          * 채점을 위한 정보를 입력해주세요.
        </div>

        {/* 날짜, 과목명 카드 */}
        <Card className="absolute w-[390px] h-[345px] top-[285px] left-9 rounded-[10px] border border-solid border-black shadow-md">
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
                className="w-full text-[20px] placeholder:text-gray-400 border-none rounded-none focus-visible:ring-0"
                placeholder="과목명-분반 형태로 입력해주세요"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
              />
              <Separator className="absolute bottom-1 bg-black h-[2px] w-[90%] ml-2" />
            </div>
          </CardContent>
        </Card>

        {/* 문제 입력 */}
        <div className="absolute left-[575px] top-[284px]">
          {answers.map((answer, index) => (
            <div key={index} className="mb-6">
              <div className="flex items-center mb-2">
                <span className="text-3xl font-bold mr-4 w-8">{index + 1}.</span>

                {/* 꼬리문제 없는 경우에만 답변/배점/체크박스 보여줌 */}
                {answer.tailQuestions.length === 0 && (
                  <>
                    <div className="w-[400px] border-b-2 border-black">
                      <input
                        type="text"
                        placeholder="Enter the answer"
                        value={answer.text}
                        onChange={(e) => {
                          const updated = [...answers];
                          updated[index].text = e.target.value;
                          setAnswers(updated);
                        }}
                        className="w-full text-xl bg-transparent focus:outline-none placeholder-gray-400"
                      />
                    </div>
                    <div className="flex items-center">
                      <input
                        type="number"
                        value={answer.point}
                        onChange={(e) => {
                          const updated = [...answers];
                          updated[index].point = parseInt(e.target.value) || 0;
                          setAnswers(updated);
                        }}
                        className="w-[100px] border-b-2 border-black bg-transparent text-lg focus:outline-none ml-2"
                        placeholder="Point"
                      />
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
                  </>
                )}

                {/* 드롭다운은 항상 표시 */}
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
              </div>

              {/* 꼬리문제 입력란 */}
              <div className="ml-10 flex flex-col items-start">
                {answer.tailQuestions.map((q, idx) => (
                  <div key={idx} className="flex items-center mb-2">
                    <span className="text-lg font-semibold mr-2">({idx + 1})</span>

                    {/* 꼬리문제 답변 입력 */}
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

                    {/* 꼬리문제 배점 입력 */}
                    <input
                      type="number"
                      value={q.point}
                      onChange={(e) => {
                        const updated = [...answers];
                        updated[index].tailQuestions[idx].point = parseInt(e.target.value) || 0;
                        setAnswers(updated);
                      }}
                      className="w-[100px] border-b-2 border-black text-lg bg-transparent focus:outline-none mr-2"
                      placeholder="Enter point"
                    />

                    {/* 꼬리문제 체크박스: 메인문제 타입이 객관식/단답형일 때만 */}
                    {(answer.type === "객관식" || answer.type === "단답형") && (
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
                    )}

                    
                  </div>
                ))}

                {/* 꼬리문제 추가/삭제 */}
                <div className="flex gap-2 mt-2">
                  <Button
                    onClick={() => addTailQuestion(index)}
                    className="bg-[#c7c7f0] hover:bg-[#b5b5e0] text-white text-sm px-4 py-1 rounded"
                  >
                    꼬리문제 추가
                  </Button>
                  <Button
                    onClick={() => removeTailQuestion(index)}
                    className="bg-[#f2bcbc] hover:bg-[#e1a9a9] text-white text-sm px-4 py-1 rounded"
                  >
                    꼬리문제 삭제
                  </Button>
                </div>
              </div>
            </div>
          ))}

          {/* 버튼 영역 */}
          <div className="flex gap-4 mt-6">
            <Button
              onClick={addAnswerField}
              className="bg-[#c7aee7] hover:bg-[#b79dd6] text-white text-xl px-4 py-2 rounded"
            >
              번호 추가
            </Button>
            <Button
              onClick={removeAnswerField}
              className="bg-[#e7aeca] hover:bg-[#d69dba] text-white text-xl px-4 py-2 rounded"
            >
              번호 삭제
            </Button>
            <Button
              onClick={handleSubmit}
              className="bg-[#a2c7e7] hover:bg-[#8db9de] text-white text-xl px-4 py-2 rounded ml-[450px]"
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
