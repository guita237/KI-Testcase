import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, TextField, Typography, CircularProgress, Alert, Box, Container, Paper, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle } from "@mui/material";
import { ArrowLeft } from "lucide-react";
import { getUserProfile, updateEmail, deleteUser } from "../services/authService";

export default function Profile() {
    const [user, setUser] = useState<{
        id: string;
        name: string;
        email: string;
        phone_number: string | null;
        role: string;
        created_at: string;
    } | null>(null);
    const [newEmail, setNewEmail] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false); // Zustand für das Lösch-Dialogfenster
    const navigate = useNavigate();

    // Profil des Benutzers laden
    useEffect(() => {
        const fetchUserProfile = async () => {
            setIsLoading(true);
            try {
                const response = await getUserProfile();
                setUser(response.user); // Extraire l'objet `user` de la réponse
            } catch (error) {
                setError("Fehler beim Laden des Profils. Bitte melden Sie sich erneut an.");
                console.error("Fehler beim Laden des Profils:", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchUserProfile();
    }, []);

    // E-Mail-Adresse aktualisieren
    const handleUpdateEmail = async () => {
        if (!newEmail.trim()) {
            setError("Bitte geben Sie eine neue E-Mail-Adresse ein.");
            return;
        }
        setIsLoading(true);
        setError(null);
        setSuccess(null);
        try {
            await updateEmail(newEmail);
            setSuccess("E-Mail-Adresse erfolgreich aktualisiert. Bitte überprüfen Sie Ihre E-Mails, um die neue Adresse zu bestätigen.");
            setNewEmail("");
            // Profil neu laden, um die aktualisierte E-Mail anzuzeigen
            const response = await getUserProfile();
            setUser(response.user);
        } catch (error) {
            setError("Fehler beim Aktualisieren der E-Mail-Adresse. Bitte versuchen Sie es erneut.");
            console.error("Fehler beim Aktualisieren der E-Mail-Adresse:", error);
        } finally {
            setIsLoading(false);
        }
    };

    // Benutzerkonto löschen
    const handleDeleteAccount = async () => {
        setIsLoading(true);
        setError(null);
        try {
            await deleteUser(); // Benutzer löschen
            localStorage.removeItem("token"); // Token aus dem localStorage entfernen
            navigate("/login"); // Weiterleitung zur Login-Seite
        } catch (error) {
            setError("Fehler beim Löschen des Benutzerkontos. Bitte versuchen Sie es erneut.");
            console.error("Fehler beim Löschen des Benutzerkontos:", error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Container maxWidth="md" className="mt-8">
            <Paper elevation={3} className="p-6">
                {/* Button "Zurück" */}
                <Button
                    startIcon={<ArrowLeft size={20} />}
                    onClick={() => navigate(-1)}
                    className="mb-4"
                >
                    Zurück
                </Button>

                <Typography variant="h4" className="mb-6">Profil</Typography>

                {isLoading && (
                    <Box display="flex" justifyContent="center" className="mb-4">
                        <CircularProgress />
                    </Box>
                )}

                {error && (
                    <Alert severity="error" className="mb-4">
                        {error}
                    </Alert>
                )}

                {success && (
                    <Alert severity="success" className="mb-4">
                        {success}
                    </Alert>
                )}

                {user && (
                    <Box className="mb-6">
                        <Typography variant="h6" className="mb-2">
                            Name: <strong>{user.name}</strong>
                        </Typography>
                        <Typography variant="h6" className="mb-2">
                            E-Mail: <strong>{user.email}</strong>
                        </Typography>
                        <Typography variant="h6" className="mb-2">
                            Telefonnummer: <strong>{user.phone_number || "Nicht angegeben"}</strong>
                        </Typography>
                        <Typography variant="h6" className="mb-2">
                            Rolle: <strong>{user.role}</strong>
                        </Typography>
                        <Typography variant="h6" className="mb-2">
                            Mitglied seit: <strong>{new Date(user.created_at).toLocaleDateString()}</strong>
                        </Typography>
                    </Box>
                )}

                <Typography variant="h6" className="mb-4">E-Mail-Adresse aktualisieren</Typography>
                <TextField
                    label="Neue E-Mail-Adresse"
                    fullWidth
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    className="mb-4"
                />
                <Button
                    variant="contained"
                    color="primary"
                    onClick={handleUpdateEmail}
                    disabled={isLoading}
                    className="w-full sm:w-auto"
                >
                    {isLoading ? <CircularProgress size={24} /> : "E-Mail aktualisieren"}
                </Button>

                {/* Button zum Löschen des Kontos */}
                <Box mt={4}>
                    <Button
                        variant="contained"
                        color="error"
                        onClick={() => setIsDeleteDialogOpen(true)}
                        disabled={isLoading}
                        className="w-full sm:w-auto"
                    >
                        Konto löschen
                    </Button>
                </Box>

                {/* Dialogfenster zur Bestätigung der Kontolöschung */}
                <Dialog
                    open={isDeleteDialogOpen}
                    onClose={() => setIsDeleteDialogOpen(false)}
                >
                    <DialogTitle>Konto löschen</DialogTitle>
                    <DialogContent>
                        <DialogContentText>
                            Sind Sie sicher, dass Sie Ihr Konto löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden.
                        </DialogContentText>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setIsDeleteDialogOpen(false)} color="primary">
                            Abbrechen
                        </Button>
                        <Button onClick={handleDeleteAccount} color="error" disabled={isLoading}>
                            {isLoading ? <CircularProgress size={24} /> : "Löschen"}
                        </Button>
                    </DialogActions>
                </Dialog>
            </Paper>
        </Container>
    );
}