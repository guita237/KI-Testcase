import { useEffect } from "react";

const useActivityDetector = (onActivity: () => void, inactivityTimeout: number) => {
    useEffect(() => {
        let inactivityTimer: number;

        const resetTimer = () => {
            clearTimeout(inactivityTimer);
            inactivityTimer = window.setTimeout(onActivity, inactivityTimeout);
        };


        window.addEventListener("mousemove", resetTimer);
        window.addEventListener("keydown", resetTimer);
        window.addEventListener("click", resetTimer);

        //
        resetTimer();

        return () => {
            clearTimeout(inactivityTimer);
            window.removeEventListener("mousemove", resetTimer);
            window.removeEventListener("keydown", resetTimer);
            window.removeEventListener("click", resetTimer);
        };
    }, [onActivity, inactivityTimeout]);
};

export default useActivityDetector;