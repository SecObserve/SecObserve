import { styled } from "@mui/system";
import { AutocompleteInput, PasswordInput, TextInput, defaultTheme } from "react-admin";
import { tss } from "tss-react";

export const AutocompleteInputExtraWide = styled(AutocompleteInput)({
    width: "45em",
});

export const AutocompleteInputWide = styled(AutocompleteInput)({
    width: "30em",
});

export const AutocompleteInputMedium = styled(AutocompleteInput)({
    width: "15em",
});

export const TextInputExtraWide = styled(TextInput)({
    width: "45em",
});

export const TextInputWide = styled(TextInput)({
    width: "30em",
});

export const PasswordInputWide = styled(PasswordInput)({
    width: "30em",
});

export function getLinkColor(setting_theme: string) {
    if (setting_theme == "dark") {
        return "#6ed2f0";
    } else {
        return "#008BBC";
    }
}

export const useLinkStyles = tss.withParams<{ setting_theme: string }>().create(({ setting_theme }) => ({
    link: {
        color: getLinkColor(setting_theme),
        textDecoration: "none",
        ":visited": {
            color: getLinkColor(setting_theme),
        },
        wordBreak: "break-word",
    },
}));

export const useStyles = tss.create({
    displayFontSize: {
        fontSize: "0.875rem",
    },
    fontBigBold: {
        fontWeight: "bold",
        fontSize: "1rem",
    },
    tabFont: {
        fontSize: "0.875rem",
        fontWeight: 500,
        lineHeight: 1.25,
        letterSpacing: "0.02857em",
    },
});

export const darkTheme = {
    palette: {
        primary: {
            main: "#6ed2f0",
        },
        secondary: {
            main: "#ff008c",
        },
        background: {
            default: "#313131",
        },
        mode: "dark" as const, // Switching the dark mode on is a single property value change.
    },
    sidebar: {
        width: 200,
    },
    components: {
        ...defaultTheme.components,
        MuiAppBar: {
            styleOverrides: {
                colorSecondary: {
                    color: "#ffffffb3",
                    backgroundColor: "#616161e6",
                },
            },
        },
        MuiTextField: {
            defaultProps: {
                variant: "outlined" as const,
            },
        },
        RaToolbar: {
            styleOverrides: {
                root: {
                    backgroundColor: "#ffffff1f",
                },
            },
        },
    },
};

export const lightTheme = {
    palette: {
        primary: {
            main: "#1e194b",
        },
        secondary: {
            light: "#5f5fc4",
            main: "#ff008c",
            dark: "#001064",
            contrastText: "#fff",
        },
        background: {
            default: "#fafafb",
        },
        mode: "light" as const,
    },
    shape: {
        borderRadius: 10,
    },
    sidebar: {
        width: 200,
    },
    components: {
        ...defaultTheme.components,
        RaReferenceField: {
            styleOverrides: {
                root: {
                    "& .RaReferenceField-link>*": {
                        color: "#008BBC",
                        ":visited": {
                            color: "#008BBC",
                        },
                    },
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                elevation1: {
                    boxShadow: "none",
                },
                root: {
                    border: "1px solid #e0e0e3",
                    backgroundClip: "padding-box",
                },
            },
        },
        MuiAppBar: {
            styleOverrides: {
                colorSecondary: {
                    color: "#808080",
                    backgroundColor: "#fff",
                },
            },
        },
        MuiLinearProgress: {
            styleOverrides: {
                colorPrimary: {
                    backgroundColor: "#f5f5f5",
                },
                barColorPrimary: {
                    backgroundColor: "#d7d7d7",
                },
            },
        },
        MuiTextField: {
            defaultProps: {
                variant: "outlined" as const,
            },
        },
    },
};
