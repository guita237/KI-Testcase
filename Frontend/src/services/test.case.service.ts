import axiosInstance from "../api/axiosInstance";
import { handleAxiosError } from "./apiErrorHandler";
import { AxiosError } from "axios";

/**
 * Ruft alle Testfälle ab, die zu den Projekten des Benutzers gehören.
 */
export async function getAllTestCases() {
    try {
        const response = await axiosInstance.get("/test-cases");
        console.log("Testfälle geladen:", response.data);
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Fehler beim Abrufen der Testfälle:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

/**
 * Ruft einen bestimmten Testfall anhand seiner ID ab.
 */
export async function getTestCaseById(testCaseId: number) {
    try {
        const response = await axiosInstance.get(`/test-cases/${testCaseId}`);
        console.log(`Testfall ${testCaseId} geladen:`, response.data);
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error(`Fehler beim Abrufen des Testfalls ${testCaseId}:`, error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

/**
 * Ruft alle Testfälle eines bestimmten Projekts ab.
 */
export async function getTestCasesByProject(projectId: number) {
    try {
        const response = await axiosInstance.get(`/test/test-cases/project/${projectId}`);
        console.log(`Testfälle für Projekt ${projectId} geladen:`, response.data);
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error(`Fehler beim Abrufen der Testfälle für Projekt ${projectId}:`, error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

/**
 * Ruft alle `requirement_text`-Einträge eines bestimmten Projekts ab.
 */
export async function getRequirementsByProject(projectId: number) {
    try {
        const response = await axiosInstance.get(`/test/requirements/project/${projectId}`);
        console.log(`Requirements für Projekt ${projectId} geladen:`, response.data);
        return response.data.requirements;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error(`Fehler beim Abrufen der Requirements für Projekt ${projectId}:`, error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}



/**
 * Ruft alle als redundant markierten Testfälle ab.
 */
export async function getRedundantTestCases() {
    try {
        const response = await axiosInstance.get("/test-cases/redundant");
        console.log("Redundante Testfälle geladen:", response.data);
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Fehler beim Abrufen redundanter Testfälle:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

/**
 * Ruft alle Testfälle mit einer bestimmten Priorität ab.
 */
export async function getTestCasesByPriority(priority: string) {
    try {
        const response = await axiosInstance.get(`/test-cases/priority/${priority}`);
        console.log(`Testfälle mit Priorität '${priority}' geladen:`, response.data);
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error(`Fehler beim Abrufen der Testfälle mit Priorität '${priority}':`, error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

/**
 * Ruft alle Testfälle mit einem bestimmten `requirement_text` ab.
 */
export async function getTestCasesByRequirement(requirementText: string) {
    try {
        const response = await axiosInstance.get(`/test/test-cases/requirement`, {
            params: { requirement_text: requirementText }
        });
        console.log(`Testfälle mit Requirement '${requirementText}' geladen:`, response.data);
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error(`Fehler beim Abrufen der Testfälle mit Requirement '${requirementText}':`, error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

/**
 * Erstellt einen neuen Testfall basierend auf einem Anforderungstext oder einer hochgeladenen Datei.
 */
export async function createTestCase(projectId: number, requirementText: string, file?: File) {
    try {
        const formData = new FormData();
        formData.append("project_id", String(projectId));
        if (requirementText) {
            formData.append("requirements_text", requirementText);
        }
        if (file) {
            formData.append("requirement_file", file);
        }

        const response = await axiosInstance.post("/generate-test-cases", formData, {
            headers: { "Content-Type": "multipart/form-data" }
        });

        console.log("Testfall erstellt:", response.data);
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Fehler beim Erstellen eines Testfalls:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

/**
 * Löscht einen Testfall anhand seiner ID.
 */
export async function deleteTestCase(testCaseId: number) {
    try {
        const response = await axiosInstance.delete(`/test/test-cases/${testCaseId}`);
        console.log(`Testfall ${testCaseId} gelöscht:`, response.data);
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error(`Fehler beim Löschen des Testfalls ${testCaseId}:`, error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

/**
 * Löscht alle Testfälle eines bestimmten Projekts.
 */
export async function deleteTestCasesByProject(projectId: number) {
    try {
        const response = await axiosInstance.delete(`/test-cases/project/${projectId}`);
        console.log(`Alle Testfälle für Projekt ${projectId} gelöscht:`, response.data);
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error(`Fehler beim Löschen der Testfälle für Projekt ${projectId}:`, error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

/**
 * Löscht alle als redundant markierten Testfälle.
 */
export async function deleteRedundantTestCases() {
    try {
        const response = await axiosInstance.delete("/delete-redundant-test-cases");
        console.log("Redundante Testfälle gelöscht:", response.data);
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Fehler beim Löschen redundanter Testfälle:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}
