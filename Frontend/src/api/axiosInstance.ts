import axios from "axios";
import { logoutUser } from "../context/Authcontext"; // Importiere logoutUser aus dem AuthContext


const API_BASE_URL = "/api";

const axiosInstance = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
    timeout: 60000,
});

axiosInstance.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("token");
        if (token) {
            config.headers["Authorization"] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        console.error("Fehler im Request-Interceptor:", error);
        return Promise.reject(error);
    }
);

axiosInstance.interceptors.response.use(
    (response) => response,
    (error) => {
        const originalRequest = error.config;


        if (error.response && error.response.status === 401 && !originalRequest._retry) {
            console.warn("Token ist abgelaufen oder ungültig. Benutzer wird abgemeldet.");
            logoutUser(); // Benutzer automatisch abmelden
            return Promise.reject(error); // Fehler weitergeben
        }

        return Promise.reject(error);
    }
);
export default axiosInstance;