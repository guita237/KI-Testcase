import { AxiosError } from "axios";


export function handleAxiosError(error: unknown): Error {
    if (error instanceof AxiosError) {
        if (error.response) {
            return new Error(error.response.data?.error || `HTTP Fehler: ${error.response.status}`);
        } else if (error.request) {
            return new Error("Keine Antwort vom Server.");
        } else {
            return new Error(`Fehler: ${error.message}`);
        }
    }
    return new Error("Unbekannter Fehler.");
}
