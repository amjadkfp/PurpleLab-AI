/**
 * Design tokens for PurpleLab AI.
 *
 * Palette is built around the platform's actual name and concept: Purple
 * Team = Red Team (offense) + Blue Team (defense) fused. Rather than a
 * single bright accent on black, we run two opposing accents - magenta
 * (attacker_sim / red) and cyan (defender / blue) - that visually resolve
 * into the purple brand color wherever attacker and defender activity
 * meet (the Timeline's central spine, the Attack Graph edges). That
 * duality is the signature visual motif used throughout the dashboard.
 */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        void: "#0A0A12",
        panel: "#12121F",
        "panel-raised": "#181828",
        "panel-border": "#26263D",
        ink: "#E8E6F0",
        "ink-muted": "#8B8A9E",
        "red-team": "#F43F5E",
        "red-team-dim": "#7A1F30",
        "blue-team": "#22D3EE",
        "blue-team-dim": "#0F5A69",
        purple: {
          DEFAULT: "#8B5CF6",
          bright: "#A78BFA",
          dim: "#4C3384",
        },
        sev: {
          critical: "#F43F5E",
          high: "#FB923C",
          medium: "#FBBF24",
          low: "#8B8A9E",
          info: "#5C5B70",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "IBM Plex Mono", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "grid-overlay":
          "linear-gradient(rgba(139,92,246,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(139,92,246,0.05) 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "28px 28px",
      },
    },
  },
  plugins: [],
};
