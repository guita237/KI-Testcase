import axiosInstance from "../api/axiosInstance";
import { handleAxiosError } from "./apiErrorHandler";
import { AxiosError } from "axios";

export async function createProject(name: string, description?: string) {
    try {
        const response = await axiosInstance.post("/projects/create-project", {
            name,
            description,
        });
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Projekt Erstellung Fehler:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

export async function getUserProjects() {
    try {
        const response = await axiosInstance.get("/projects/user-projects");
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Fehler beim Abrufen der Projekte:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

export async function getProject(projectId: number) {
    try {
        const response = await axiosInstance.get(`/projects/project/${projectId}`);
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Fehler beim Abrufen des Projekts:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

export async function updateProject(projectId: number, name: string, description?: string) {
    try {
        const response = await axiosInstance.put(`/projects/update-project/${projectId}`, {
            name,
            description,
        });
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Fehler beim Aktualisieren des Projekts:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

export async function deleteProject(projectId: number) {
    try {
        const response = await axiosInstance.delete(`/projects/delete-project/${projectId}`);
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Fehler beim Löschen des Projekts:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}