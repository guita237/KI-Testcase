// AppRouter.tsx
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "../pages/Login";
import Register from "../pages/Register";
import Dashboard from "../pages/Dashboard";
import Profile from "../pages/Profile";
import AuthProvider from "../context/Authcontext";
import LogsPage from "../pages/LogsPage";
import KISuggestionsPage from "../pages/KISuggestionsPage";

import TestCaseManagementPage from "../pages/Testcasepage.tsx";


const AppRouter = () => {


    return (
        <AuthProvider>
            <Router>
                <Routes>
                    <Route path="/" element={<Login />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/profile" element={<Profile />} />
                    <Route path="/project/:projectId" element={<TestCaseManagementPage/>} />
                    <Route path="/logs" element={<LogsPage />} />
                    <Route path="/ki-suggestions" element={<KISuggestionsPage />} />
                </Routes>
            </Router>
        </AuthProvider>
    );
};

export default AppRouter;