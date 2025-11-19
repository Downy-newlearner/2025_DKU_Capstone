import axios from "axios";
import config from "../config";

// 토큰 로컬스토리지에서 꺼내기
const token = localStorage.getItem("token");

const instance = axios.create({
  baseURL: config.api.baseURL,
  timeout: config.api.timeout,
  withCredentials: config.api.withCredentials,
  headers: {
    Authorization: token ? `Bearer ${token}` : "", // ✅ 여기에 기본 Authorization 설정
  },
});

export default instance;