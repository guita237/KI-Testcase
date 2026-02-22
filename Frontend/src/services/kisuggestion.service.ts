import axiosInstance from "../api/axiosInstance";
import { handleAxiosError } from "./apiErrorHandler";
import { AxiosError } from "axios";

// Alle KI-Vorschläge abrufen
export async function getKISuggestions() {
    try {
        const response = await axiosInstance.get("/ki-suggestions/ki-suggestions");
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Fehler beim Abrufen der KI-Vorschläge:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

// KI-Vorschlag löschen
export async function deleteKISuggestion(suggestionId: number) {
    try {
        const response = await axiosInstance.delete(`/ki-suggestions/${suggestionId}`);
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Fehler beim Löschen des KI-Vorschlags:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}
