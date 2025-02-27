import React from 'react';
import Login from './components/Login'; // Login 컴포넌트 import
import './App.css'; // Tailwind를 적용하기 위해 유지

function App() {
  return (
    <div className="App">
      <Login /> {/* 초기 화면 대신 Login 컴포넌트 렌더링 */}
    </div>
  );
}
export default App;

