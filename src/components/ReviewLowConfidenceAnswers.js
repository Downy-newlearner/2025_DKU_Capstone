import React, { useEffect, useState } from "react";
import axios from "../api/axios";
import { Input } from "./ui/input";
import { Button } from "./ui/button";

const ReviewAnswers = () => {
  const [images, setImages] = useState([]);

  useEffect(() => {
    axios.get("/api/low-confidence-images")
      .then(res => setImages(res.data)) // [{ id, base64 }]
      .catch(err => console.error(err));
  }, []);

  const handleInputChange = (id, value) => {
    setImages(prev =>
      prev.map(img => img.id === id ? { ...img, answer: value } : img)
    );
  };

  const handleSubmit = () => {
    const payload = images.map(({ id, answer }) => ({ id, answer }));
    axios.post("/api/submit-corrections", payload)
      .then(() => alert("답안이 성공적으로 제출되었습니다!"))
      .catch(err => console.error("제출 오류:", err));
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      {images.map((img, index) => (
        <div key={img.id} className="flex flex-col items-center gap-2 border rounded-lg p-4 shadow-sm">
          <img
            src={`data:image/png;base64,${img.base64}`}
            alt={`image-${index}`}
            className="w-full max-w-sm max-h-[200px] object-contain border"
          />
          <Input
            type="text"
            placeholder="이미지에 쓰여 있는 답을 입력해주세요"
            value={img.answer || ""}
            onChange={(e) => handleInputChange(img.id, e.target.value)}
            className="w-full max-w-sm"
          />
        </div>
      ))}
      {images.length > 0 && (
        <div className="text-center">
          <Button onClick={handleSubmit}>제출하기</Button>
        </div>
      )}
    </div>
  );
};

export default ReviewAnswers;
