import { createContext, useContext, useEffect, useState } from "react";
import { login, logout, getUserProfile } from "../services/authService";

type AuthContextType = {
    user: any | null;
    loginUser: (email: string, password: string) => Promise<void>;
    logoutUser: () => void;
    userProfile: any | null;
};

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

 const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = useState<any | null>(null);
    const [userProfile, setUserProfile] = useState<any | null>(null);

    //  Neue Funktion: Prüft, ob der Token abgelaufen ist
    const checkTokenExpiration = () => {
        const token = localStorage.getItem("token");
        if (!token) {
            return;
        }

        try {
            const payload = JSON.parse(atob(token.split('.')[1])); // Dekodiere das JWT Payload
            const expiryTime = payload.exp * 1000; // Ablaufzeit in Millisekunden
            if (Date.now() >= expiryTime) {
                console.log("Token ist abgelaufen – Benutzer wird automatisch ausgeloggt.");
                logoutUser();
            }
        } catch (error) {
            console.error("Fehler beim Dekodieren des Tokens:", error);
            logoutUser(); // Sicherheitshalber ausloggen, falls das Token ungültig ist
        }
    };

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (token) {
            setUser({ token });
            fetchUserProfile();
            checkTokenExpiration(); // Sofort beim Laden prüfen
        }

        // Prüft alle 5 Minuten, ob das Token noch gültig ist
        const interval = setInterval(checkTokenExpiration, 5 * 60 * 1000);

        return () => clearInterval(interval); // Intervall beim Unmounten aufräumen
    }, []);

    const fetchUserProfile = async () => {
        try {
            const profile = await getUserProfile();
            setUserProfile(profile);
        } catch (error) {
            console.error("Fehler beim Laden des Benutzerprofils:", error);
        }
    };

    const loginUser = async (email: string, password: string) => {
        try {
            const response = await login(email, password);
            localStorage.setItem("token", response.token);
            setUser({ token: response.token });
            fetchUserProfile();
        } catch (error) {
            throw error; // Fehler weitergeben, damit UI es anzeigen kann
        }
    };

    const logoutUser = () => {
        logout(); // Optional: Backend-Logout aufrufen
        setUser(null);
        setUserProfile(null);
        localStorage.removeItem("token"); // Token aus dem localStorage entfernen
        window.location.href = "/login"; // Weiterleitung zur Login-Seite
    };

    return (
        <AuthContext.Provider value={{ user, loginUser, logoutUser, userProfile }}>
            {children}
        </AuthContext.Provider>
    );
};

//  Export für Logout außerhalb von AuthProvider
export const logoutUser = () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth muss innerhalb eines AuthProviders verwendet werden!");
    }
    return context;
};
export default AuthProvider;