import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
    Drawer, IconButton, List, ListItemText, Avatar,
    Divider, ListItemButton, Box
} from "@mui/material";
import {
    Menu as MenuIcon, User, LogOut, Book,
    ArrowLeft, LayoutDashboard, FileText,
} from "lucide-react";

export default function Menu() {
    const [open, setOpen] = useState(false);
    const navigate = useNavigate();
    const { projectId } = useParams<{ projectId: string }>();

    const toggleMenu = () => setOpen(!open);
    const handleNavigation = (path: string) => {
        navigate(path);
        setOpen(false);
    };

    return (
        <>

            <Box sx={{ position: "fixed", top: 16, left: 16, zIndex: 1300 }}>
                <IconButton onClick={toggleMenu} sx={{ color: "gray.700" }}>
                    <MenuIcon size={28} />
                </IconButton>
            </Box>


            <Drawer anchor="left" open={open} onClose={toggleMenu}>
                <div className="p-4 flex flex-col h-full bg-gray-900 text-white w-64">
                    <div className="flex items-center justify-between mb-6">
                        <Avatar className="bg-blue-500">
                            <User size={24} />
                        </Avatar>
                        <IconButton onClick={toggleMenu} className="text-white">
                            <ArrowLeft size={24} />
                        </IconButton>
                    </div>

                    <List className="flex-grow">
                        {projectId && (
                            <ListItemButton
                                onClick={() => handleNavigation(`/project/${projectId}`)}
                                className="hover:bg-gray-800"
                            >
                                <FileText size={20} className="mr-3" />
                                <ListItemText primary="Projektseite" />
                            </ListItemButton>
                        )}
                        <ListItemButton
                            onClick={() => handleNavigation("/logs")}
                            className="hover:bg-gray-800"
                        >
                            <Book size={20} className="mr-3" />
                            <ListItemText primary="Logs" />
                        </ListItemButton>
                        <ListItemButton
                            onClick={() => handleNavigation("/dashboard")}
                            className="hover:bg-gray-800"
                        >
                            <LayoutDashboard size={20} className="mr-3" />
                            <ListItemText primary="Dashboard" />
                        </ListItemButton>
                    </List>

                    <Divider className="bg-gray-700 my-4" />

                    <List>
                        <ListItemButton
                            onClick={() => handleNavigation("/profile")}
                            className="hover:bg-gray-800"
                        >
                            <User size={20} className="mr-3" />
                            <ListItemText primary="Profil" />
                        </ListItemButton>
                        <ListItemButton
                            onClick={() => {
                                localStorage.removeItem("token");
                                handleNavigation("/login");
                            }}
                            className="hover:bg-gray-800"
                        >
                            <LogOut size={20} className="mr-3" />
                            <ListItemText primary="Abmelden" />
                        </ListItemButton>
                    </List>
                </div>
            </Drawer>
        </>
    );
}
