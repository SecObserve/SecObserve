import react from "eslint-plugin-react";
import typescriptEslint from "@typescript-eslint/eslint-plugin";
import security from "eslint-plugin-security";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tsParser from "@typescript-eslint/parser";
import js from "@eslint/js";

export default [
    js.configs.recommended,
    {
        files: ["**/*.tsx", "**/*.ts"],
        plugins: {
            react,
            "@typescript-eslint": typescriptEslint,
            security,
            "react-hooks": reactHooks,
        },
        languageOptions: {
            globals: {
                ...globals.browser,
            },
            parser: tsParser,
            ecmaVersion: "latest",
            sourceType: "module",
            parserOptions: {
                project: "./tsconfig.json",
                ecmaFeatures: {
                    jsx: true,
                },
            },
        },
        settings: {
            react: {
                pragma: "React",
                version: "19",
            },
        },
        rules: {
            // React recommended rules
            ...react.configs.recommended.rules,
            ...react.configs["jsx-runtime"].rules,
            
            // TypeScript recommended rules
            // ...typescriptEslint.configs["strict-type-checked"].rules,
            ...typescriptEslint.configs.recommended.rules,
            ...typescriptEslint.configs["stylistic-type-checked"].rules,

            // Security recommended rules
            ...security.configs.recommended.rules,
            
            // React Hooks recommended rules
            ...reactHooks.configs.recommended.rules,
            
            // Custom overrides
            "@typescript-eslint/consistent-type-definitions": "off",
            "@typescript-eslint/no-explicit-any": "off",
            "@typescript-eslint/prefer-nullish-coalescing": "off",
            "react/display-name": "off",
            "react/jsx-key": "off",
            "react-hooks/immutability": "off",
            "react-hooks/purity": "off",
            "react-hooks/refs": "off",
            "react-hooks/set-state-in-effect": "off",
            "react-hooks/static-components": "off",
        },
    }
];