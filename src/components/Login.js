import React from "react";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Checkbox } from "./ui/checkbox";
import { Input } from "./ui/input";
import { EyeOff } from "lucide-react";
console.log(Button);



export default function Login() {
  return (
    <div className="bg-white flex flex-row justify-center w-full min-h-screen">
      <div className="w-full max-w-[1440px] relative py-[30px] px-[42px]">
        <div className="font-semibold text-black text-xl">
          Your Logo
        </div>

        <div className="flex gap-12 mt-[84px] px-[69px]">
          <Card className="w-[505px] border-[#868686] border-[0.5px] shadow-lg">
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
                      className="h-[59px] text-sm font-light"
                      placeholder="Enter your user Email"
                    />
                  </div>

                  <div className="relative">
                    <div className="text-black text-base mb-2">
                      Password
                    </div>
                    <div className="relative">
                      <Input
                        type="password"
                        className="h-[59px] text-sm font-light"
                        placeholder="Enter your Password"
                      />
                      <EyeOff className="absolute right-4 top-1/2 -translate-y-1/2 w-[21px] h-[21px] text-gray-500" />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Checkbox id="remember" className="w-[15px] h-[15px] border-black" />
                    <label htmlFor="remember" className="font-light text-black text-xs">
                      Remember me
                    </label>
                  </div>
                  <button className="font-light text-[#4c4c4c] text-xs">
                    Forgot Password?
                  </button>
                </div>

                <Button className="w-full h-[57px] bg-black text-white font-medium text-base">
                  Login
                </Button>

                <div className="flex justify-center gap-2 mt-[55px]">
                  <span className="font-light text-[#7d7d7d] text-base">
                    Don't have an Account?
                  </span>
                  <button className="font-semibold text-[#7d7d7d] text-base">
                    Register
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex-1">
            <img
              className="w-[827px] h-[650px] object-contain"
              alt="Small team discussing ideas"
              src="/login.png"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
