import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom"; // Importiere useNavigate für den Rückkehr-Button
import {
    Typography,
    List,
    ListItem,
    CircularProgress,
    Card,
    CardContent,
    Box,
    IconButton,
} from "@mui/material";
import { Trash2, ArrowLeft } from "lucide-react"; // Icons für Löschen und Rückkehr
import { deleteKISuggestion, getKISuggestions } from "../services/kisuggestion.service.ts";
import Menu from "../components/Menu.tsx";

export default function KISuggestionsPage() {
    const [kiSuggestions, setKISuggestions] = useState<{ message: string } | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const navigate = useNavigate(); // Hook pour la navigation

    // KI-Vorschläge laden
    useEffect(() => {
        const fetchKISuggestions = async () => {
            try {
                const kiData = await getKISuggestions();
                if (kiData && typeof kiData === "object" && "message" in kiData) {
                    setKISuggestions(kiData);
                } else {
                    setKISuggestions({ message: "Ein Problem ist aufgetreten." });
                }
            } catch (error) {
                console.error("Fehler beim Laden der KI-Vorschläge:", error);
                setKISuggestions({ message: "Fehler beim Laden von KI-Vorschlägen." });
            } finally {
                setIsLoading(false);
            }
        };
        fetchKISuggestions();
    }, []);

    // KI-Vorschlag löschen
    const handleDelete = async (suggestionId: number) => {
        try {
            await deleteKISuggestion(suggestionId);
            setKISuggestions((prev) => prev?.message ? prev : { message: "KI-Vorschlag gelöscht." });
        } catch (error) {
            console.error("Fehler beim Löschen des KI-Vorschlags:", error);
        }
    };

    // Funktion zur Rückkehr zur vorherigen Seite
    const handleGoBack = () => {
        navigate(-1); // Gehe eine Seite zurück
    };

    return (
        <div className="flex min-h-screen bg-gray-900 text-white">
            {/* Menu-Komponente */}
            <Menu />

            {/* Hauptinhalt der Seite */}
            <div className="flex flex-col items-center p-6 w-full overflow-y-auto bg-gray-50">
                {/* Button zur Rückkehr zur vorherigen Seite */}
                <Box display="flex" justifyContent="flex-start" width="100%" maxWidth="4xl" className="mb-4">
                    <IconButton onClick={handleGoBack} className="text-gray-900">
                        <ArrowLeft size={24} />
                    </IconButton>
                </Box>

                <Typography variant="h4" className="mb-4 text-gray-900">KI-Vorschläge</Typography>
                {isLoading ? (
                    <CircularProgress />
                ) : (
                    <List className="w-full max-w-4xl">
                        {kiSuggestions && kiSuggestions.message ? (
                            <ListItem className="mb-2">
                                <Card className="w-full shadow-lg">
                                    <CardContent>
                                        <Box display="flex" alignItems="center" justifyContent="space-between">
                                            <Box>
                                                <Typography variant="h6" className="font-bold text-gray-900">
                                                    {kiSuggestions.message}
                                                </Typography>
                                            </Box>
                                            <IconButton onClick={() => handleDelete(0)} disabled>
                                                <Trash2 size={20} className="text-red-500" />
                                            </IconButton>
                                        </Box>
                                    </CardContent>
                                </Card>
                            </ListItem>
                        ) : (
                            <Typography variant="h6" className="text-gray-500">
                                No suggestions available.
                            </Typography>
                        )}
                    </List>
                )}
            </div>
        </div>
    );
}
