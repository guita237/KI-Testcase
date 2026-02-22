import { useEffect, useState } from "react";
import { getUserProjects, createProject, updateProject, deleteProject } from "../services/projectService";
import { Button, Card, TextField, Typography, IconButton, Avatar, Menu, MenuItem, Modal, Box } from "@mui/material";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { ToastContainer, toast } from "react-toastify";
import { PlusCircle, User, MoreVertical } from "lucide-react";
import "react-toastify/dist/ReactToastify.css";

export default function Dashboard() {
    const navigate = useNavigate();
    const [projects, setProjects] = useState<any[]>([]);
    const [newProjectName, setNewProjectName] = useState("");
    const [newProjectDescription, setNewProjectDescription] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [menuAnchor, setMenuAnchor] = useState<{ anchor: HTMLElement | null; projectId: number | null }>({ anchor: null, projectId: null });
    const open = Boolean(anchorEl);
    const [modalOpen, setModalOpen] = useState(false);
    const [editMode, setEditMode] = useState(false);
    const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (!token) {
            navigate("/login");
            return;
        }
        fetchProjects();
    }, []);

    async function fetchProjects() {
        try {
            const response = await getUserProjects();
            setProjects(response.projects);
        } catch (error: any) {
            toast.error(error.message || "Fehler beim Laden der Projekte.");
        }
    }

    async function handleCreateOrUpdateProject() {
        if (!newProjectName.trim()) {
            toast.error("Projektname ist erforderlich.");
            return;
        }
        setIsLoading(true);
        try {
            if (editMode && selectedProjectId) {
                await updateProject(selectedProjectId, newProjectName, newProjectDescription);
                toast.success("Projekt erfolgreich aktualisiert!");
            } else {
                await createProject(newProjectName, newProjectDescription);
                toast.success("Projekt erfolgreich erstellt!");
            }
            setNewProjectName("");
            setNewProjectDescription("");
            setEditMode(false);
            setSelectedProjectId(null);
            fetchProjects();
            setModalOpen(false);
        } catch (error: any) {
            toast.error(error.message || "Fehler beim Erstellen/Aktualisieren des Projekts.");
        } finally {
            setIsLoading(false);
        }
    }

    async function handleDeleteProject(projectId: number) {
        try {
            await deleteProject(projectId);
            toast.success("Projekt erfolgreich gelöscht!");
            fetchProjects();
        } catch (error: any) {
            toast.error(error.message || "Fehler beim Löschen des Projekts.");
        }
    }

    return (
        <div className="min-h-screen flex flex-col items-center bg-gray-900 text-white p-6 relative">
            {/* Profile Menu */}
            <div className="absolute top-4 left-4">
                <IconButton onClick={(e) => setAnchorEl(e.currentTarget)}>
                    <Avatar className="bg-blue-500"><User size={24} /></Avatar>
                </IconButton>
                <Menu
                    anchorEl={anchorEl}
                    open={open}
                    onClose={() => setAnchorEl(null)}
                >
                    <MenuItem onClick={() => navigate("/profile")}>
                        Profil ansehen
                    </MenuItem>
                    <MenuItem onClick={() => {
                        localStorage.removeItem("token");
                        navigate("/login");
                    }}>
                        Abmelden
                    </MenuItem>
                </Menu>
            </div>

            {/* Hauptbereich */}
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7 }}
                className="w-full max-w-4xl"
            >
                <Typography variant="h3" className="text-center mb-6">
                    Dashboard
                </Typography>

                {/* Projekt erstellen Button mit Modal */}
                <div className="flex justify-center mb-6">
                    <Button
                        variant="contained"
                        color="primary"
                        startIcon={<PlusCircle size={20} />}
                        onClick={() => { setModalOpen(true); setEditMode(false); }}
                    >
                        Neues Projekt erstellen
                    </Button>
                </div>

                {/* Modal für neues oder bestehendes Projekt */}
                <Modal open={modalOpen} onClose={() => setModalOpen(false)}>
                    <Box className="bg-white p-6 rounded-lg shadow-lg w-96 mx-auto mt-32">
                        <Typography variant="h5" className="mb-4">{editMode ? "Projekt bearbeiten" : "Neues Projekt"}</Typography>
                        <TextField
                            label="Projektname"
                            fullWidth
                            value={newProjectName}
                            onChange={(e) => setNewProjectName(e.target.value)}
                            className="mb-3"
                        />
                        <TextField
                            label="Beschreibung (optional)"
                            fullWidth
                            value={newProjectDescription}
                            onChange={(e) => setNewProjectDescription(e.target.value)}
                            className="mt-3 mb-3"
                        />
                        <Button
                            variant="contained"
                            color="primary"
                            fullWidth
                            onClick={handleCreateOrUpdateProject}
                            disabled={isLoading}
                        >
                            {isLoading ? "Erstelle..." : editMode ? "Speichern" : "Projekt erstellen"}
                        </Button>
                    </Box>
                </Modal>

                {/* Projektübersicht mit Optionen */}
                <Typography variant="h5" className="mb-4">Meine Projekte</Typography>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {projects.map((project) => (
                        <Card
                            key={project.id}
                            className="bg-gray-800 p-4 rounded-lg shadow-md relative flex justify-between items-center hover:bg-gray-700 transition"
                        >
                            {/* Zone click for project*/}
                            <div
                                className="flex-1 cursor-pointer"
                                onClick={() => navigate(`/project/${project.id}`)}
                            >
                                <Typography variant="h6">{project.name}</Typography>
                                <Typography variant="body2" className="text-gray-400">
                                    {project.description || "Keine Beschreibung"}
                                </Typography>
                            </div>

                            {/* Button for 3 points */}
                            <IconButton
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setMenuAnchor({ anchor: e.currentTarget, projectId: project.id });
                                }}
                            >
                                <MoreVertical size={20} />
                            </IconButton>

                            {/* Menu options */}
                            <Menu
                                anchorEl={menuAnchor.anchor}
                                open={menuAnchor.projectId === project.id}
                                onClose={() => setMenuAnchor({ anchor: null, projectId: null })}
                            >
                                <MenuItem onClick={(e) => {
                                    e.stopPropagation();
                                    setEditMode(true);
                                    setSelectedProjectId(project.id);
                                    setNewProjectName(project.name);
                                    setNewProjectDescription(project.description || "");
                                    setModalOpen(true);
                                }}>
                                    Bearbeiten
                                </MenuItem>
                                <MenuItem onClick={(e) => {
                                    e.stopPropagation();
                                    handleDeleteProject(project.id);
                                }}>
                                    Löschen
                                </MenuItem>
                            </Menu>
                        </Card>
                    ))}
                </div>

            </motion.div>
            <ToastContainer />
        </div>
    );
}
