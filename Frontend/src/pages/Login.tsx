import { useState, useContext } from "react";
import { useNavigate, Link } from "react-router-dom";
import { TextField, Button, Typography, Card, IconButton, InputAdornment, Modal, Box } from "@mui/material";
import { Visibility, VisibilityOff } from "@mui/icons-material";
import { ToastContainer, toast } from "react-toastify";
import { AuthContext } from "../context/Authcontext";
import { motion } from "framer-motion";
import { resetPassword } from "../services/authService";
import "react-toastify/dist/ReactToastify.css";

export default function Login() {
    const authContext = useContext(AuthContext);
    if (!authContext) throw new Error("AuthContext must be provided!");

    const { loginUser } = authContext;
    const navigate = useNavigate();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
    const [isLoading, setIsLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [resetEmail, setResetEmail] = useState("");
    const [isResetModalOpen, setIsResetModalOpen] = useState(false);

    const togglePasswordVisibility = () => setShowPassword(!showPassword);

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setErrors({});
        setIsLoading(true);

        try {
            await loginUser(email, password);
            toast.success("Successfully logged in!", { theme: "dark", autoClose: 3000 });
            setTimeout(() => navigate("/dashboard"), 3000);
        } catch (error: any) {
            toast.error(error.message, { theme: "dark", autoClose: 5000 });

            if (error.message.includes("400")) setErrors({ email: "Email required!", password: "Password required!" });
            else if (error.message.includes("401")) setErrors({ email: "Invalid email!", password: "Wrong password!" });
            else if (error.message.includes("404")) setErrors({ email: "User not found!" });
        } finally {
            setIsLoading(false);
        }
    };

    const handleResetPassword = async () => {
        if (!resetEmail.trim()) {
            toast.error("Please enter a valid email address.", { theme: "dark", autoClose: 4000 });
            return;
        }

        try {
            await resetPassword(resetEmail);
            toast.success("Reset link sent!", { theme: "dark", autoClose: 4000 });
            setTimeout(() => {
                setIsResetModalOpen(false);
                setResetEmail("");
            }, 4000);
        } catch (error) {
            toast.error("Failed to reset password.", { theme: "dark", autoClose: 4000 });
        }
    };

    return (
        <div className="min-h-screen flex justify-center items-center bg-gradient-to-br from-gray-900 via-blue-900 to-black">
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7 }}
                className="w-full max-w-lg p-4"
            >
                <Card className="bg-white/90 backdrop-blur-md shadow-2xl rounded-2xl p-8 border border-gray-700">
                    <Typography variant="h4" className="mb-6 text-center font-bold text-gray-900">
                        Login
                    </Typography>

                    <form onSubmit={handleSubmit}>
                        <TextField
                            label="Email"
                            type="email"
                            fullWidth
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            autoComplete="off"
                            error={!!errors.email}
                            helperText={errors.email}
                            sx={{ mb: 3 }}
                        />

                        <TextField
                            label="Password"
                            type={showPassword ? "text" : "password"}
                            fullWidth
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            autoComplete="off"
                            error={!!errors.password}
                            helperText={errors.password}
                            sx={{ mb: 3 }}
                            InputProps={{
                                endAdornment: (
                                    <InputAdornment position="end">
                                        <IconButton onClick={togglePasswordVisibility}>
                                            {showPassword ? <VisibilityOff /> : <Visibility />}
                                        </IconButton>
                                    </InputAdornment>
                                ),
                            }}
                        />

                        <Button variant="text" onClick={() => setIsResetModalOpen(true)} sx={{ mb: 2 }}>
                            Forgot Password?
                        </Button>

                        <Button variant="contained" fullWidth type="submit" disabled={isLoading}>
                            {isLoading ? "Logging in..." : "Login"}
                        </Button>
                    </form>

                    <Typography className="mt-4 text-center text-sm">
                        No account yet? <Link to="/register" className="text-blue-400 hover:underline">Register here</Link>
                    </Typography>
                </Card>
            </motion.div>

            <Modal open={isResetModalOpen} onClose={() => setIsResetModalOpen(false)}>
                <Box className="bg-white p-6 rounded-lg shadow-xl w-96 mx-auto mt-32">
                    <Typography variant="h6" className="mb-4 text-center">
                        Reset Password
                    </Typography>
                    <TextField
                        label="Enter your email..."
                        fullWidth
                        value={resetEmail}
                        onChange={(e) => setResetEmail(e.target.value)}
                    />
                    <Button onClick={handleResetPassword} variant="contained" fullWidth sx={{ mt: 2 }}>
                        Confirm
                    </Button>
                </Box>
            </Modal>

            <ToastContainer />
        </div>
    );
}
