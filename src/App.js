import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './components/Login'; // Login 컴포넌트 import
import SignUp from './components/SignUp';
import Main from "./components/Main";
import Mypage from "./components/Mypage";
import Grading from "./components/Grading";
import ChangePassword from "./components/ChangePassword";
import ForgetPassword from "./components/ForgetPassword";
import AuthenticatePassword from "./components/AuthenticatePassword";
import GradingInformation from "./components/GradingInformation";
import StudentIdPending from "./components/StudentIdPending";
import GradingPending from "./components/GradingPending";
import UploadStudentAnswer from "./components/UploadStudentAnswer";
import ReviewLowConfidenceAnswers from "./components/ReviewLowConfidenceAnswers";
import GradingSecondPending from "./components/GradingSecondPending";
import PastResultsPage from "./components/PastResultsPage";
import ReviewLowConfidenceStudentIds from "./components/ReviewLowConfidenceStudentIds";
import GradingResults from "./components/GradingResults";
import SubjectZipList from "./components/SubjectZipList";


import './App.css'; // Tailwind를 적용하기 위해 유지

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/subject-zip-list" element={<SubjectZipList />} />
        <Route path="/grading-results" element={<GradingResults />} />
        <Route path="/past-results" element={<PastResultsPage />} />
        <Route path="/grading-second-pending" element={<GradingSecondPending />} />
        <Route path="/review-answers" element={<ReviewLowConfidenceAnswers />} />
        <Route path="/grading-pending" element={<GradingPending />} />
        <Route path="/review-low-confidence-ids" element={<ReviewLowConfidenceStudentIds />} />
        <Route path="/student-id-pending" element={<StudentIdPending />} />
        <Route path="/upload-answer" element={<UploadStudentAnswer />} />
        <Route path="/grading-info" element={<GradingInformation />} />
        <Route path="/reset-password" element={<AuthenticatePassword />} />
        <Route path="/forgetpassword" element={<ForgetPassword />} />
        <Route path="/changepassword" element={<ChangePassword />} />
        <Route path="/grading" element={<Grading />} />
        <Route path="/mypage" element={<Mypage />} />
        <Route path="/main" element={<Main />} /> 
        <Route path="/signup" element={<SignUp />} />
        <Route path="/" element={<Login />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
