import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    build: {
        outDir: "build",
        rolldownOptions: {
            output: {
                strictExecutionOrder: true,
            },
        },
    },
    server: {
        port: 3000,
        strictPort: true,
    },
});
