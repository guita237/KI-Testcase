import axiosInstance from "../api/axiosInstance";
import { handleAxiosError } from "./apiErrorHandler";
import axios, { AxiosError } from "axios";

export interface Clarification {
    needs_clarification: boolean;
    questions: string[];
    suggested_updates?: string;
}

export interface TestCase {
    id: number;
    name: string;
    full_description: string;
    format: 'classic' | 'bdd';
    created_at: string;
    requirement_text: string;
}

export interface GenerateTestCasesResponse {
    success: boolean;
    message: string;
    test_cases?: TestCase[];
    warnings?: string[];
    clarification?: Clarification;
}

export async function generateTestCases(
    requirementsText: string,
    projectId: number,
    format: 'classic' | 'bdd' = 'classic'
): Promise<GenerateTestCasesResponse> {
    const payload = {
        requirements_text: requirementsText,
        project_id: projectId,
        format
    };

    console.log("Sending payload:", JSON.stringify(payload, null, 2));

    try {
        const response = await axiosInstance.post<GenerateTestCasesResponse>(
            '/ai/generate-test-cases',
            payload
        );

        const data = response.data;

        if (data?.clarification?.needs_clarification) {
            console.warn("Clarification needed:", data.clarification);
            return {
                success: false,
                message: data.message ?? "Requirement needs clarification",
                clarification: data.clarification,
                test_cases: [],
                warnings: data.warnings ?? []
            };
        }

        if (data?.test_cases && data.test_cases.length > 0) {
            return {
                success: true,
                message: data.message ?? "Test cases generated successfully",
                test_cases: data.test_cases,
                warnings: data.warnings ?? []
            };
        }

        return {
            success: false,
            message: data?.message ?? "No test cases generated and no clarification provided.",
            test_cases: [],
            warnings: data.warnings ?? []
        };

    } catch (error) {
        if (axios.isAxiosError(error)) {
            const errorData = error.response?.data;
            console.error("API Error Details:", {
                status: error.response?.status,
                data: errorData,
                headers: error.response?.headers
            });

            throw new Error(
                errorData?.error ||
                errorData?.message ||
                `HTTP Error: ${error.response?.status}`
            );
        }

        console.error("Unexpected error:", error);
        throw new Error("An unexpected error occurred");
    }
}



export async function generateTestScript(projectId: number, requirementText: string, framework: string = "pytest") {
    try {
        const response = await axiosInstance.post(`/ai/generate-test-script`, {
            project_id: projectId,
            requirement_text: requirementText,
            framework: framework,
        });
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Test Script Generation Fehler:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

export async function prioritizeTestCases(projectId: number, requirementText: string) {
    try {
        const response = await axiosInstance.post(`/ai/prioritize-test-cases`, {
            project_id: projectId,
            requirement_text: requirementText,
        });
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Test Case Prioritization Fehler:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

export async function classifyRequirements(projectId: number, requirementText?: string, classifyAll: boolean = false) {
    try {
        const response = await axiosInstance.post(`/ai/classify-requirements`, {
            project_id: projectId,
            requirement_text: requirementText,
            classify_all: classifyAll,
        });
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Requirement Classification Fehler:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

export async function findRedundantTestCases(projectId: number, requirementText: string) {
    try {
        const response = await axiosInstance.post(`/ai/find-redundant-test-cases`, {
            project_id: projectId,
            requirement_text: requirementText,
        });
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Redundant Test Case Detection Fehler:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}

export async function downloadTestScript(testCaseId: number) {
    try {
        const response = await axiosInstance.get(`/ai/download-test-script/${testCaseId}`, {
            responseType: "blob",
        });
        return response.data;
    } catch (error: unknown) {
        if (error instanceof AxiosError) {
            console.error("Test Script Download Fehler:", error.response?.data || error.message);
        }
        throw handleAxiosError(error);
    }
}
