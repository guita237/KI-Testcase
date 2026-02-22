import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom"; // Importiere useLocation
import {
    Typography,
    List,
    ListItem,
    CircularProgress,
    Card,
    CardContent,
    Avatar,
    Box,
    IconButton,
} from "@mui/material";
import { Folder, Create, Update, Delete, ArrowLeft } from "@mui/icons-material"; // Icons für Aktionen und Rückkehr
import { getLogsByUser } from "../services/logs.service.ts";
import Menu from "../components/Menu"; // Importiere das Menu-Komponent
import gsap from "gsap"; // Importiere GSAP für Animationen


const AnimatedList = React.forwardRef<HTMLUListElement, React.ComponentProps<typeof List>>(
    (props, ref) => {
        return <List {...props} ref={ref} />;
    }
);

export default function LogsPage() {
    const [logs, setLogs] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const navigate = useNavigate();
    const logsRef = useRef<HTMLUListElement>(null); // Ref für die Logs-Liste (HTMLUListElement)

    // Effekt, um die Logs zu laden, wenn die Seite geladen wird
    useEffect(() => {
        console.log("LogsPage geladen"); // Überprüfe, ob die Seite gerendert wird

        const token = localStorage.getItem("token");
        if (!token) {
            console.error("Benutzer ist nicht authentifiziert. Weiterleitung zur Login-Seite...");
            navigate("/login"); // Weiterleitung zur Login-Seite
            return;
        }

        const fetchLogs = async () => {
            try {
                const logsData = await getLogsByUser();
                console.log("Logs geladen:", logsData);
                setLogs(logsData.logs); // Greife auf das Array `logs` in der Antwort zu
            } catch (error) {
                console.error("Fehler beim Laden der Logs:", error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchLogs();
    }, [navigate]);

    // GSAP-Animation für die Logs
    useEffect(() => {
        if (!isLoading && logsRef.current) {
            // Animation für die Logs-Liste
            gsap.from(logsRef.current.children, {
                opacity: 0,
                y: 20,
                stagger: 0.1, // Verzögerung zwischen den Elementen
                duration: 0.5,
                ease: "power2.out",
            });
        }
    }, [isLoading]);

    // Funktion zur Formatierung des Datums
    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString("de-DE", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        });
    };

    // Funktion zur Auswahl des Icons basierend auf der Aktion
    const getActionIcon = (action: string) => {
        switch (action) {
            case "Projekt erstellt":
                return <Create />;
            case "Projekt aktualisiert":
                return <Update />;
            case "Projekt gelöscht":
                return <Delete />;
            default:
                return <Folder />;
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
                <Box
                    display="flex"
                    justifyContent="flex-start"
                    alignItems="center"
                    width="100%"
                    maxWidth="4xl"
                    className="mb-4"
                    sx={{ mt: '50px' }} // descendre un peu pour éviter le menu
                >
                    <IconButton onClick={handleGoBack} className="text-gray-900">
                        <ArrowLeft sx={{ fontSize: 24 }} />
                    </IconButton>
                </Box>


                <Typography variant="h4" className="mb-4 text-gray-900">Logs</Typography>
                {isLoading ? (
                    <CircularProgress />
                ) : (
                    <AnimatedList className="w-full max-w-4xl" ref={logsRef}>
                        {logs.map((log, index) => (
                            <ListItem key={index} className="mb-2">
                                <Card className="w-full shadow-lg">
                                    <CardContent>
                                        <Box display="flex" alignItems="center">
                                            <Avatar className="mr-3 bg-blue-500">
                                                {getActionIcon(log.action)}
                                            </Avatar>
                                            <Box>
                                                <Typography variant="h6" className="font-bold text-gray-900">
                                                    {log.action}
                                                </Typography>
                                                <Typography variant="body2" className="text-gray-600">
                                                    {log.description}
                                                </Typography>
                                                <Typography variant="caption" className="text-gray-400">
                                                    {formatDate(log.created_at)}
                                                </Typography>
                                            </Box>
                                        </Box>
                                    </CardContent>
                                </Card>
                            </ListItem>
                        ))}
                    </AnimatedList>
                )}
            </div>
        </div>
    );
}