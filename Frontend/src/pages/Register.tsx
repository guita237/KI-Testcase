import { useState, useContext, useEffect, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { TextField, Button, Typography, Card, IconButton, InputAdornment } from "@mui/material";
import { Visibility, VisibilityOff } from "@mui/icons-material";
import { ToastContainer, toast } from "react-toastify";
import { AuthContext } from "../context/Authcontext";
import { motion } from "framer-motion";
import "react-toastify/dist/ReactToastify.css";
import { gsap } from "gsap";
import { registerUser } from "../services/authService";

export default function Register() {
    const navigate = useNavigate();
    const authContext = useContext(AuthContext);
    if (!authContext) {
        throw new Error("AuthContext wurde nicht richtig bereitgestellt!");
    }

    // State für Formulardaten
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [errors, setErrors] = useState<{ name?: string; email?: string; password?: string }>({});
    const [isLoading, setIsLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    // Referenz für GSAP-Animationen
    const formRef = useRef(null);

    useEffect(() => {
        gsap.from(formRef.current, {opacity: 0, y: 50, duration: 1, ease: "power3.out"});
    }, []);

    const togglePasswordVisibility = () => {
        setShowPassword((prev) => !prev);
    };

    // Funktion zur Validierung des Formulars
    const validateForm = () => {
        const newErrors: { name?: string; email?: string; password?: string } = {};
        if (!name.trim()) newErrors.name = "Name ist erforderlich!";
        if (!email.trim()) newErrors.email = "E-Mail ist erforderlich!";
        if (!password.trim()) newErrors.password = "Passwort ist erforderlich!";
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    // Funktion zur Registrierung eines Benutzers
    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (!validateForm()) return;

        setIsLoading(true);

        try {
            await registerUser(name, email, password);
            toast.success("Ein Verifizierungslink wurde an Ihre E-Mail gesendet!", {theme: "dark", autoClose: 5000});
            setTimeout(() => navigate("/login"), 5000);
        } catch (error: any) {
            toast.error("Fehler bei der Registrierung.", {theme: "dark", autoClose: 7000});
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div
            className="min-h-screen flex justify-center items-center bg-gradient-to-br from-gray-900 via-blue-900 to-black">
            <motion.div
                initial={{opacity: 0, y: 30}}
                animate={{opacity: 1, y: 0}}
                transition={{duration: 0.7}}
                className="w-full max-w-lg p-4"
            >
                <Card className="bg-white/90 backdrop-blur-md shadow-2xl rounded-2xl p-8 border border-gray-700">
                    <Typography variant="h4" className="mb-6 text-center font-bold text-gray-900">
                        Registrierung
                    </Typography>

                    <form onSubmit={handleSubmit}>
                        <TextField
                            label="Name"
                            fullWidth
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            error={!!errors.name}
                            helperText={errors.name}
                            sx={{mb: 3}}
                        />

                        <TextField
                            label="E-Mail"
                            type="email"
                            fullWidth
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            error={!!errors.email}
                            helperText={errors.email}
                            sx={{mb: 3}}
                        />

                        <TextField
                            label="Passwort"
                            type={showPassword ? "text" : "password"}
                            fullWidth
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            error={!!errors.password}
                            helperText={errors.password}
                            sx={{mb: 3}}
                            InputProps={{
                                endAdornment: (
                                    <InputAdornment position="end">
                                        <IconButton onClick={togglePasswordVisibility}>
                                            {showPassword ? <VisibilityOff/> : <Visibility/>}
                                        </IconButton>
                                    </InputAdornment>
                                ),
                            }}
                        />

                        <Button variant="contained" fullWidth type="submit" disabled={isLoading}>
                            {isLoading ? "Registrierung läuft..." : "Registrieren"}
                        </Button>
                    </form>

                    <Typography className="mt-4 text-center text-sm">
                        Bereits ein Konto? <Link to="/login" className="text-blue-400 hover:underline">Hier
                        einloggen</Link>
                    </Typography>
                </Card>
            </motion.div>

            <ToastContainer/>
        </div>
    );
}
