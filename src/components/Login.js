import React, { useState } from "react";
import { useNavigate } from "react-router-dom"; // 페이지 이동을 위한 Hook
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Input } from "./ui/input";
import { EyeIcon, EyeOffIcon } from "lucide-react";
console.log(Button);

const Login = () => {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({
    email: '',
    password: ''
  });
  const [errorMessage, setErrorMessage] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleLogin = async () => {
    try {
      const response = await fetch("http://13.209.197.61:8080/sign-in", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // 필요 시
        body: JSON.stringify({
          email : form.email,
          password : form.password
        }),
      });

      if (!response.ok) {
        throw new Error("로그인 요청 실패");
      }

      const contentType = response.headers.get("content-type");
      let data = null;

      if (contentType && contentType.includes("application/json")) {
        data = await response.json();
      } else {
        data = {};
      }

      if (!data.accessToken) {
        throw new Error("로그인 실패: 토큰이 없습니다.");
      }

      console.log("로그인 성공!", data); 

      localStorage.setItem("token", data.accessToken);
      navigate("/main");
    } catch (err) {
      setErrorMessage(err.message);
      console.error("로그인 오류:", err.message);
    }
  };

  return (
    <div className="bg-white flex flex-row justify-center w-full min-h-screen">
      <div className="w-full max-w-[1440px] relative py-[30px] px-[42px]">
      <div className="w-[120px] h-auto">
        <img src="/Checkmate5.png" alt="Logo" className="object-contain w-full" />
      </div>


        <div className="flex flex-row mt-[29px] px-[69px]">
          <Card className="w-[505px] h-[757px] rounded-[10px] border-[0.5px] border-solid border-[#868686] shadow-lg">
            <CardContent className="p-[35px]">
              <div className="font-light text-black text-[25px]">
                Welcome!
              </div>

              <div className="mt-[68px]">
                <div className="font-medium text-black text-[31px]">
                  Sign in to
                </div>
                <div className="text-black text-base mt-3">
                  CheckMate
                </div>
              </div>

              <div className="mt-[48px] space-y-[38px]">
                <div className="space-y-[33px]">
                  <div>
                    <div className="text-black text-base mb-2">
                      Email
                    </div>
                    <Input
                      name="email"
                      className="h-[59px] text-sm font-light"
                      placeholder="Enter your user Email"
                      value={form.email}
                      onChange={handleChange}
                    />
                  </div>

                  <div className="relative">
                    <div className="text-black text-base mb-2">
                      Password
                    </div>
                    <div className="relative">
                      <Input
                        name="password"
                        type={showPassword ? "text" : "password"}
                        className="h-[59px] text-sm font-light"
                        placeholder="Enter your Password"
                        value={form.password}
                        onChange={handleChange}
                      />
                       <button
                          className="absolute right-[28px] top-[50%] transform -translate-y-1/2"
                          onClick={() => setShowPassword(!showPassword)}
                      >
                          {showPassword ? (
                              <EyeOffIcon className="absolute right-1 top-1/2 -translate-y-1/2 w-[21px] h-[21px] text-gray-500" />
                          ) : (
                              <EyeIcon className="absolute right-1 top-1/2 -translate-y-1/2 w-[21px] h-[21px] text-gray-500" />
                          )}
                      </button>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <button className="font-light text-[#4c4c4c] text-xs"
                  onClick={() => navigate("/forgetpassword")} // 클릭 시 이동
                  >
                    Forgot Password?
                  </button>
                </div>

                <Button className="mt-[79px] h-[57px] w-full bg-[#c7aee7] text-white rounded-md hover:bg-[#c7aee7]/90 text-base font-medium"
                onClick={handleLogin}
                >
                  Login
                </Button>

                <div className="flex justify-center gap-2 mt-[55px]">
                  <span className="font-light text-[#7d7d7d] text-base">
                    Don't have an Account?
                  </span>
                  <button className="font-semibold text-[#7d7d7d] text-base"
                  onClick={() => {navigate("/signup")}} // 클릭 시 SignUp 페이지로 이동
                  >
                    Register
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex-1 flex items-center justify-center ml-[60px]">
            <img
              className="w-[551px] h-[551px] object-contain"
              alt="Small team discussing ideas"
              src="/loginimage1.png"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
