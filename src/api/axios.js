import axios from "axios";

// 토큰 로컬스토리지에서 꺼내기
const token = localStorage.getItem("token");

const instance = axios.create({
  baseURL: "http://13.209.197.61:8080",
  withCredentials: true,
  headers: {
    Authorization: token ? `Bearer ${token}` : "", // ✅ 여기에 기본 Authorization 설정

  },
});

export default instance;