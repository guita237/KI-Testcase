import axiosInstance from "../api/axiosInstance";
import { handleAxiosError } from "./apiErrorHandler";
import { AxiosError } from "axios";

// Benutzer-Logs abrufen
export async function getLogsByUser() {
    try {
        const response = await axiosInstance.get("/logs/logs/user");
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Fehler beim Abrufen der Logs:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}