import React, { useState } from "react";
import { useNavigate } from "react-router-dom"; // 페이지 이동을 위한 Hook
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Input } from "./ui/input";
import { EyeIcon, EyeOffIcon } from "lucide-react";
import { signup } from "../api/auth";


const SignUp = () => {
  const navigate = useNavigate(); // useNavigate 훅 사용
  const [showPassword, setShowPassword] = useState(false); // 추가
  const [showConfirmPassword, setShowConfirmPassword] = useState(false); // 추가
  const [form, setForm] = useState({
    email: '',
    name: '',
    password: '',
    confirmPassword: '',
  });

  const togglePasswordVisibility = () => {
    setShowPassword((prev) => !prev);
  };

  const toggleConfirmPasswordVisibility = () => {
    setShowConfirmPassword((prev) => !prev);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleRegister = async () => {
    console.log("✅ handleRegister 함수 실행됨!");
    if (form.password !== form.confirmPassword) {
      alert("비밀번호가 일치하지 않습니다.");
      return;
    }

    console.log("📦 회원가입 요청 데이터:", form);
    
    try {
      await signup({
        email: form.email,    //email
        name: form.name,//username
        password: form.password,
      });
      alert("회원가입 성공!");
      navigate("/"); // 로그인 페이지로 이동
    } catch (err) {
      console.error(err);
      alert("회원가입 실패");
    }
  };


  return (
    <div className="bg-white flex flex-row justify-center w-full min-h-screen">
      <div className="bg-white w-full max-w-[1440px] relative py-[30px] px-[42px]">
      <div className="w-[120px] h-auto">
        <img src="/Checkmate5.png" alt="Logo" className="object-contain w-full" />
      </div>


        <div className="flex flex-row mt-[29px] px-[69px]">
          <Card className="w-[505px] h-[757px] rounded-[10px] border-[0.5px] border-solid border-[#868686] shadow-lg">
            <CardContent className="pt-[10px] px-[35px] pb-[35px]">
              <div className="font-light text-black text-[25px] mt-[10px]">Welcome!</div>

              <div className="mt-[15px]">
                <div className="font-medium text-black text-[31px] leading-normal">
                  Sign up to
                </div>
                <div className="text-black text-base mt-2">CheckMate</div>
              </div>

              <div className="mt-[30px]">
                <div>
                  <label className="font-normal text-black text-base leading-normal block mb-[8px]">
                    Email
                  </label>
                  <Input
                    name="email"
                    value={form.email}
                    onChange={handleChange}
                    placeholder="Enter your email"
                    className="h-[59px] rounded-md border-[0.6px] border-solid border-[#282828] px-[16px] py-[17px] font-light text-[#ababab] text-sm mb-[25px]"
                  />
                </div>

                <div>
                  <label className="font-normal text-black text-base leading-normal block mb-[8px]">
                    User name
                  </label>
                  <Input
                    name="name"
                    value={form.name}
                    onChange={handleChange}
                    placeholder="Enter your user name"
                    className="h-[59px] rounded-md border-[0.6px] border-solid border-[#282828] px-[16px] py-[17px] font-light text-[#ababab] text-sm mb-[25px]"
                  />
                </div>

                <div>
                  <label className="font-normal text-black text-base leading-normal block mb-[8px]">
                    Password
                  </label>
                  <div className="relative">
                    <Input
                      name="password"
                      type={showPassword ? "text" : "password"}
                      value={form.password}
                      onChange={handleChange}
                      placeholder="Enter your Password"
                      className="h-[59px] rounded-md border-[0.6px] border-solid border-[#282828] px-[16px] py-[17px] font-light text-[#ababab] text-sm mb-[25px]"
                    />
                    <button
                      className="absolute right-[28px] py-[18px]"
                      onClick={togglePasswordVisibility}
                    >
                      {showPassword ? (
                        <EyeIcon className="w-[21px] h-[21px] text-gray-500" />
                      ) : (
                        <EyeOffIcon className="w-[21px] h-[21px] text-gray-500" />
                      )}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="font-normal text-black text-base leading-normal block mb-[8px]">
                    Confrim Password
                  </label>
                  <div className="relative">
                    <Input
                      name="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      value={form.confirmPassword}
                      onChange={handleChange}
                      placeholder="Confrim your Password"
                      className="h-[59px] rounded-md border-[0.6px] border-solid border-[#282828] px-[16px] py-[17px] font-light text-[#ababab] text-sm mb-[25px]"
                    />
                    <button
                      className="absolute right-[28px] py-[18px]"
                      onClick={toggleConfirmPasswordVisibility}
                    >
                      {showConfirmPassword ? (
                        <EyeIcon className="w-[21px] h-[21px] text-gray-500" />
                      ) : (
                        <EyeOffIcon className="w-[21px] h-[21px] text-gray-500" />
                      )}
                    </button>
                  </div>
                </div>
              </div>

              <Button className="w-full h-[57px] bg-[#c7aee7] rounded-md mt-[3px] font-medium text-white text-base"
              onClick={handleRegister}>
                Register
              </Button>

              <div className="flex justify-center mt-[8px]">
                <span className="font-light text-[#7d7d7d] text-base">
                  Already have an Account?
                </span>
                <button
                  className="font-semibold text-black text-base ml-2"
                  onClick={() => navigate("/")} // 클릭 시 로그인 페이지로 이동
                >
                  Login
                </button>
              </div>
            </CardContent>
          </Card>

          <div className="flex-1 flex items-center justify-center ml-[60px]">
            <img
              className="w-[551px] h-[551px]"
              alt="Small team discussing ideas"
              src="/loginimage1.png"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default SignUp;
