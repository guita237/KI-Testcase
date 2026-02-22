import axiosInstance from "../api/axiosInstance";
import { handleAxiosError } from "./apiErrorHandler";
import { AxiosError } from "axios";


export async function login(email: string, password: string) {
    try {
        const response = await axiosInstance.post("/auth/login", { email, password });
        localStorage.setItem("token", response.data.token);
        localStorage.setItem("userId", response.data.userId);
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Login Fehler:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

export async function resetPassword(email: string) {
    try {
        const response = await axiosInstance.post("/auth/reset-password", { email });
        return response.data;
    } catch (error) {
        console.error("Fehler beim Zurücksetzen des Passworts:", error);
        throw handleAxiosError(error);
    }
}

export async function registerUser(name: string, email: string, password: string) {
    try {
        const response = await axiosInstance.post("/auth/register", {
            name,
            email,
            password,
        });
        return response.data;
    } catch (error) {
        throw handleAxiosError(error);
    }
}



export const getUserProfile = async () => {
    try {
        const response = await axiosInstance.get("/users/get-user");
        return response.data;
    } catch (error: unknown) {
        throw handleAxiosError(error);
    }
};

export const updateEmail = async (newEmail: string) => {
    try {
        const response = await axiosInstance.post("/auth/update-email", { new_email: newEmail });
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Fehler beim Aktualisieren der E-Mail:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
};

export const logout = () => {
    try {
        localStorage.removeItem("token");
    } catch (error: unknown) {
        console.error("Fehler beim Logout:", error);
    }
};

export const deleteUser = async () => {
    try {
        const response = await axiosInstance.delete("/auth/delete-user");
        return response.data;
    } catch (error: unknown) {
        throw handleAxiosError(error);
    }
}


