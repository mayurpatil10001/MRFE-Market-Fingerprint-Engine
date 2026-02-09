export default {
    content: ["./index.html", "./src/**/*.{ts,tsx}"],
    theme: {
        extend: {
            colors: {
                ink: "#0f1f2f",
                ocean: "#104e8b",
                mint: "#19d3a2",
                coral: "#ff6f61",
                cloud: "#f2f7fb",
                sunset: "#f59f6f",
                dusk: "#233244",
                haze: "#f7f3ea",
            },
            fontFamily: {
                display: ["Space Grotesk", "sans-serif"],
                body: ["IBM Plex Sans", "sans-serif"],
                mono: ["IBM Plex Mono", "monospace"],
            },
            boxShadow: {
                panel: "0 14px 40px rgba(10, 40, 68, 0.12)",
            },
        },
    },
    plugins: [],
};
