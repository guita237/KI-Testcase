import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Menu from "../components/Menu";
import {
    Button, Card, TextField, Typography, CircularProgress,
    MenuItem, Collapse, IconButton, Select, FormControl,
    InputLabel, Dialog, DialogActions, DialogContent,
    DialogContentText, DialogTitle, InputAdornment, Box,
    Chip, Divider, Tooltip, Alert, AlertTitle
} from "@mui/material";
import { motion } from "framer-motion";
import { ToastContainer, toast } from "react-toastify";
import {
    ChevronDown, ChevronUp, Search,
    Trash2, Copy, FileText, TestTube2
} from "lucide-react";
import "react-toastify/dist/ReactToastify.css";


// Services
import {
    getTestCasesByProject,
    getRequirementsByProject,
    deleteTestCasesByProject,
    deleteTestCase, getTestCasesByRequirement,
} from "../services/test.case.service.ts";
import { generateTestCases } from "../services/aiService.ts";

// Types
interface TestCase {
    id: number;
    name: string;
    full_description: string;
    format: 'classic' | 'bdd';
    created_at: string;
    requirement_text?: string;
}

interface Requirement {
    id: number;
    text: string;
}

interface ApiResponse {
    message: string;
    test_cases?: TestCase[];
    clarification?: {
        needs_clarification: boolean;
        questions: string[];
        suggested_updates: string;
    };
}

// Styles
const testCaseStyles = {
    bdd: {
        feature: { color: "#4f46e5", fontWeight: "bold" },
        scenario: { color: "#10b981", fontWeight: "bold" },
        step: { color: "#6b7280", marginLeft: "1rem" }
    },
    classic: {
        header: { color: "#3b82f6", fontWeight: "bold" },
        content: { marginLeft: "1rem" }
    }
};

/**
 * Formats a date string to a readable format
 */
const formatDate = (dateString: string) => {
    try {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return "Unknown date";
    }
};

/**
 * Detect test case format based on content
 */
const detectTestCaseFormat = (testCase: TestCase): 'classic' | 'bdd' => {
    // If format is explicitly defined, use it
    if (testCase.format) {
        return testCase.format;
    }

    // Detect BDD format by keywords
    const description = testCase.full_description || '';
    if (description.includes('Feature:') ||
        description.includes('Scenario:') ||
        description.includes('Given') ||
        description.includes('When') ||
        description.includes('Then') ||
        description.toLowerCase().includes('gherkin')) {
        return 'bdd';
    }

    // Default to classic
    return 'classic';
};


export default function TestCaseManagementPage() {
    const { projectId } = useParams();
    const [searchTerm, setSearchTerm] = useState("");
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

    // Data state
    const [testCases, setTestCases] = useState<TestCase[]>([]);
    const [requirements, setRequirements] = useState<Requirement[]>([]);
    const [selectedRequirement, setSelectedRequirement] = useState<string>("");
    const [selectedFormat, setSelectedFormat] = useState<'classic' | 'bdd'>("classic");

    // User input
    const [newRequirement, setNewRequirement] = useState("");
    const [clarification, setClarification] = useState<{
        questions: string[];
        suggestion: string;
    } | null>(null);

    // UI state
    const [isLoading, setIsLoading] = useState(false);
    const [isFetching, setIsFetching] = useState(true);
    const [showTestCases, setShowTestCases] = useState(true);

    useEffect(() => {
        fetchTestCases();
        fetchRequirements();
    }, [projectId]);

    /**
     * Validates and normalizes test case data from API
     */
    const validateTestCase = (testCase: any): TestCase => {
        const description = testCase.full_description || testCase.description || "";
        return {
            id: testCase.id || Date.now(),
            name: testCase.name || "Unnamed Test Case",
            full_description: description,
            format: testCase.format || detectTestCaseFormat({ ...testCase, full_description: description }),
            created_at: testCase.created_at || new Date().toISOString(),
            requirement_text: testCase.requirement_text
        };
    };

    // Data fetching functions
    const fetchTestCases = async () => {
        try {
            setIsFetching(true);
            const response = await getTestCasesByProject(Number(projectId));
            const validatedTestCases = response.map(validateTestCase);
            setTestCases(validatedTestCases);
        } catch (error) {
            showError("Error loading test cases", error);
        } finally {
            setIsFetching(false);
        }
    };

    const fetchRequirements = async () => {
        try {
            const response = await getRequirementsByProject(Number(projectId));

            const requirementArray = Array.isArray(response.requirements)
                ? response.requirements
                : response;

            const cleaned = requirementArray.map((req: string, index: number) => ({
                id: index + 1,
                text: req
            }));
            setRequirements(cleaned);
        } catch (error) {
            showError("Error loading requirements", error);
        }
    };


    /**
     * Handles test case generation from requirements
     */
    const handleGenerateTestCases = async () => {
        const requirementText = newRequirement.trim();
        if (!requirementText) {
            toast.error("Please enter a valid requirement");
            return;
        }

        setIsLoading(true);
        setClarification(null); // Reset previous clarifications

        try {
            const response = await generateTestCases(
                requirementText,
                Number(projectId),
                selectedFormat
            ) as ApiResponse;

            if (response.clarification && response.clarification.needs_clarification) {
                setClarification({
                    questions: response.clarification.questions || [],
                    suggestion: response.clarification.suggested_updates || requirementText
                });
                return;  // stop here, no save to DB
            }

            if (response.test_cases && response.test_cases.length > 0) {
                const validatedTestCases = response.test_cases.map(validateTestCase);
                setTestCases(prev => [...prev, ...validatedTestCases]);
                setNewRequirement("");
                toast.success(`${response.test_cases.length} test cases generated: ${response.message}`);
                await fetchRequirements();
            } else {
                toast.warning(response.message || "No test cases were generated");
            }

        } catch (error: unknown) {
            const errorMessage = error instanceof Error ?
                error.message.replace("API Error: ", "") :
                "Failed to generate test cases";
            toast.error(errorMessage);
            console.error("Generation Error:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleRequirementSelection = async (requirementText: string) => {
        setSelectedRequirement(requirementText);
        setSearchTerm(requirementText);

        if (requirementText) {
            try {
                setIsFetching(true);
                const response = await getTestCasesByRequirement(requirementText);
                const validatedTestCases = response.map(validateTestCase);
                setTestCases(validatedTestCases);
            } catch (error) {
                showError("Failed to fetch test cases for requirement", error);
            } finally {
                setIsFetching(false);
            }
        } else {
            await fetchTestCases();
        }
    };


    /**
     * Applies the suggested clarification to the requirement input
     */
    const applySuggestion = () => {
        if (clarification) {
            setNewRequirement(clarification.suggestion);
            setClarification(null);
        }
    };

    const handleDeleteTestCases = async () => {
        try {
            await deleteTestCasesByProject(Number(projectId));
            toast.success("All test cases deleted");
            setTestCases([]);
        } catch (error) {
            showError("Error deleting test cases", error);
        } finally {
            setDeleteDialogOpen(false);
        }
    };

    const handleDeleteTestCase = async (id: number) => {
        try {
            await deleteTestCase(id);
            setTestCases(prev => prev.filter(tc => tc.id !== id));
            toast.success("Test case deleted");
        } catch (error) {
            showError("Error deleting test case", error);
        }
    };

    const handleCopyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        toast.info("Copied to clipboard");
    };



    // Helper functions
    const showError = (message: string, error: unknown) => {
        console.error(message, error);
        toast.error(message);
    };



    /**
     * Renders test case content with proper formatting based on type (BDD or classic)
     */
    const renderTestCaseContent = (testCase: TestCase) => {
        try {
            if (!testCase.full_description) {
                return (
                    <Box sx={{ color: 'warning.main', p: 2, fontStyle: 'italic' }}>
                        No description available for this test case
                    </Box>
                );
            }

            const lines = testCase.full_description.split('\n');

            if (testCase.format === "bdd") {
                return (
                    <Box component="pre" sx={{
                        whiteSpace: 'pre-wrap',
                        fontFamily: 'monospace',
                        backgroundColor: '#f8fafc',
                        padding: 2,
                        borderRadius: 1
                    }}>
                        {lines.map((line, i) => {
                            const trimmedLine = line.trim();
                            if (trimmedLine.startsWith("Feature:")) {
                                return <div key={`feature-${i}`} style={testCaseStyles.bdd.feature}>{line}</div>;
                            } else if (trimmedLine.startsWith("Scenario:")) {
                                return <div key={`scenario-${i}`} style={testCaseStyles.bdd.scenario}>{line}</div>;
                            } else if (trimmedLine.match(/^(Given|When|Then|And|But)\s+/)) {
                                return <div key={`step-${i}`} style={testCaseStyles.bdd.step}>{line}</div>;
                            } else if (trimmedLine === "") {
                                return <br key={`empty-${i}`} />;
                            }
                            return <div key={`line-${i}`}>{line}</div>;
                        })}
                    </Box>
                );
            } else {
                return (
                    <Box component="pre" sx={{
                        whiteSpace: 'pre-wrap',
                        fontFamily: 'monospace',
                        backgroundColor: '#f8fafc',
                        padding: 2,
                        borderRadius: 1
                    }}>
                        {lines.map((line, i) => {
                            const trimmedLine = line.trim();
                            if (trimmedLine.match(/^(Name|Description|Prerequisites|Test Steps|Expected Result):/)) {
                                return <div key={`header-${i}`} style={testCaseStyles.classic.header}>{line}</div>;
                            } else if (trimmedLine.match(/^\d+\./)) {
                                return <div key={`step-${i}`} style={{ marginLeft: '1rem' }}>{line}</div>;
                            }
                            return <div key={`line-${i}`} style={testCaseStyles.classic.content}>{line}</div>;
                        })}
                    </Box>
                );
            }
        } catch (error) {
            console.error("Error rendering test case:", error);
            return (
                <Box sx={{ color: 'error.main', p: 2 }}>
                    Error displaying this test case
                </Box>
            );
        }
    };

    const filteredTestCases = testCases.filter(testCase => {
        if (!searchTerm.trim()) return true;
        const searchLower = searchTerm.toLowerCase();
        return (
            (testCase.name && testCase.name.toLowerCase().includes(searchLower)) ||
            (testCase.full_description && testCase.full_description.toLowerCase().includes(searchLower)) ||
            (testCase.requirement_text && testCase.requirement_text.toLowerCase().includes(searchLower))
        );
    });


    return (
        <div className="flex min-h-screen bg-gray-50">
            <Menu />
            <div className="flex flex-col items-center p-6 w-full overflow-y-auto" style={{ marginLeft: '240px' }}>
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="w-full max-w-6xl"
                >
                    {/* Header and search section */}
                    <div className="flex flex-col gap-4 mb-6">
                        <div className="flex justify-between items-center">
                            <Typography variant="h4" className="font-bold text-gray-800">
                                Test Case Management
                            </Typography>
                            <Chip
                                label={`${testCases.length} test cases`}
                                color="primary"
                                variant="outlined"
                            />
                        </div>

                        <div className="flex gap-4 items-center">
                            <div className="flex-grow">
                                <TextField
                                    variant="outlined"
                                    placeholder="Search test cases..."
                                    size="small"
                                    fullWidth
                                    InputProps={{
                                        startAdornment: (
                                            <InputAdornment position="start">
                                                <Search size={18} className="text-gray-400" />
                                            </InputAdornment>
                                        ),
                                        sx: { backgroundColor: 'background.paper' }
                                    }}
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                />
                            </div>

                            <FormControl sx={{ minWidth: 250 }}>
                                <InputLabel>Requirements</InputLabel>
                                <Select
                                    value={selectedRequirement}
                                    onChange={(e) => handleRequirementSelection(e.target.value)}
                                    label="Requirements"
                                    size="small"
                                >
                                    <MenuItem value="">
                                        <em>All requirements</em>
                                    </MenuItem>
                                    {requirements.map((requirement) => {
                                        const text = requirement.text || "";
                                        return (
                                            <MenuItem key={requirement.id} value={text}>
                                                {text.length > 50 ? `${text.substring(0, 50)}...` : text}
                                            </MenuItem>
                                        );
                                    })}
                                </Select>
                            </FormControl>
                        </div>
                    </div>



                    {/* Input section */}
                    <Card className="p-6 mb-6 shadow-sm">
                        <Typography variant="h6" className="mb-4 font-semibold text-gray-700">
                            Generate New Test Cases
                        </Typography>

                        <TextField
                            label="Requirement description"
                            fullWidth
                            multiline
                            minRows={4}
                            maxRows={8}
                            value={newRequirement}
                            onChange={(e) => setNewRequirement(e.target.value)}
                            className="mb-4"
                            placeholder="Describe the requirement for which you want to generate test cases..."
                        />

                        {/* Clarification help section (shown when API requests more details) */}
                        {clarification && (
                            <Alert
                                severity="info"
                                className="mb-4"
                                onClose={() => setClarification(null)}
                            >
                                <AlertTitle>Requirement Needs Clarification</AlertTitle>
                                <Typography variant="body2" component="div">
                                    <ul style={{ paddingLeft: '20px', margin: '8px 0' }}>
                                        {clarification.questions.map((question, index) => (
                                            <li key={index}>{question}</li>
                                        ))}
                                    </ul>
                                    <Typography variant="subtitle2" gutterBottom>
                                        Suggested improvement:
                                    </Typography>
                                    <Box component="pre" sx={{
                                        whiteSpace: 'pre-wrap',
                                        backgroundColor: '#e8f5e9',
                                        p: 2,
                                        borderRadius: 1,
                                        fontSize: '0.875rem'
                                    }}>
                                        {clarification.suggestion}
                                    </Box>
                                    <Button
                                        variant="contained"
                                        size="small"
                                        sx={{ mt: 2 }}
                                        onClick={applySuggestion}
                                    >
                                        Apply Suggestion
                                    </Button>
                                </Typography>
                            </Alert>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4 mt-4">
                            <FormControl fullWidth>
                                <InputLabel>Test case format</InputLabel>
                                <Select
                                    value={selectedFormat}
                                    onChange={(e) => setSelectedFormat(e.target.value as 'classic' | 'bdd')}
                                    label="Test case format"
                                >
                                    <MenuItem value="classic">
                                        <div className="flex items-center">
                                            <FileText size={16} className="mr-2" />
                                            Classic format
                                        </div>
                                    </MenuItem>
                                    <MenuItem value="bdd">
                                        <div className="flex items-center">
                                            <TestTube2 size={16} className="mr-2" />
                                            BDD (Gherkin)
                                        </div>
                                    </MenuItem>
                                </Select>
                            </FormControl>
                        </div>

                        <Button
                            onClick={handleGenerateTestCases}
                            disabled={isLoading}
                            variant="contained"
                            color="primary"
                            size="large"
                            fullWidth
                            className="mt-2"
                            startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : null}
                        >
                            {isLoading ? "Generating..." : "Generate Test Cases"}
                        </Button>
                    </Card>

                    {/* Test cases section */}
                    <Card className="p-0 mb-6 overflow-hidden shadow-sm">
                        <div
                            className="flex justify-between items-center p-4 bg-gray-50 hover:bg-gray-100 cursor-pointer"
                            onClick={() => setShowTestCases(!showTestCases)}
                        >
                            <div className="flex items-center">
                                <Typography variant="h6" className="font-semibold text-gray-700">
                                    Test Cases
                                </Typography>
                                <Chip
                                    label={filteredTestCases.length}
                                    color="primary"
                                    size="small"
                                    className="ml-2"
                                />
                            </div>
                            <IconButton>
                                {showTestCases ? <ChevronUp /> : <ChevronDown />}
                            </IconButton>
                        </div>

                        <Collapse in={showTestCases}>
                            <Divider />
                            <div className="divide-y">
                                {filteredTestCases.length > 0 ? (
                                    filteredTestCases.map((testCase) => (
                                        <div key={testCase.id} className="p-4 hover:bg-gray-50 transition-colors">
                                            <div className="flex justify-between items-start mb-2">
                                                <div>
                                                    <Typography variant="subtitle1" className="font-bold text-gray-800">
                                                        {testCase.name}
                                                    </Typography>
                                                    <div className="flex items-center space-x-2 mt-1">
                                                        <Chip
                                                            label={detectTestCaseFormat(testCase) === "bdd" ? "BDD" : "Classic"}
                                                            size="small"
                                                            color={detectTestCaseFormat(testCase) === "bdd" ? "success" : "primary"}
                                                            variant="outlined"
                                                            sx={{
                                                                backgroundColor: detectTestCaseFormat(testCase) === "bdd" ? '#e6ffed' : '#e6f7ff',
                                                                borderColor: detectTestCaseFormat(testCase) === "bdd" ? '#57ab5a' : '#1890ff'
                                                            }}
                                                        />
                                                        <Typography variant="caption" className="text-gray-500">
                                                            {formatDate(testCase.created_at)}
                                                        </Typography>
                                                    </div>
                                                </div>
                                                <div className="flex space-x-1">
                                                    <Tooltip title="Copy to clipboard">
                                                        <IconButton
                                                            onClick={() => handleCopyToClipboard(testCase.full_description)}
                                                            size="small"
                                                        >
                                                            <Copy size={16} />
                                                        </IconButton>
                                                    </Tooltip>
                                                    <Tooltip title="Delete test case">
                                                        <IconButton
                                                            onClick={() => handleDeleteTestCase(testCase.id)}
                                                            color="error"
                                                            size="small"
                                                        >
                                                            <Trash2 size={16} />
                                                        </IconButton>
                                                    </Tooltip>
                                                </div>
                                            </div>

                                            <Card variant="outlined" className="mt-2 p-3 bg-white">
                                                {renderTestCaseContent(testCase)}
                                            </Card>
                                        </div>
                                    ))
                                ) : (
                                    <div className="p-8 text-center">
                                        <Typography className="text-gray-500">
                                            {testCases.length === 0
                                                ? "No test cases found. Generate your first test case!"
                                                : "No matching test cases found"}
                                        </Typography>
                                    </div>
                                )}
                            </div>
                        </Collapse>
                    </Card>

                    {/* Delete confirmation dialog */}
                    <Dialog
                        open={deleteDialogOpen}
                        onClose={() => setDeleteDialogOpen(false)}
                    >
                        <DialogTitle>Confirm Deletion</DialogTitle>
                        <DialogContent>
                            <DialogContentText>
                                Are you sure you want to delete all {testCases.length} test cases for this project?
                                This action cannot be undone.
                            </DialogContentText>
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
                            <Button
                                onClick={handleDeleteTestCases}
                                color="error"
                                variant="contained"
                                startIcon={<Trash2 size={18} />}
                            >
                                Delete All
                            </Button>
                        </DialogActions>
                    </Dialog>

                    {isFetching && (
                        <div className="flex justify-center p-8">
                            <CircularProgress />
                        </div>
                    )}
                </motion.div>
                <ToastContainer position="bottom-right" autoClose={5000} />
            </div>
        </div>
    );
}