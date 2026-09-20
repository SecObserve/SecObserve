import LockIcon from "@mui/icons-material/Lock";
import PersonIcon from "@mui/icons-material/Person";
import { Avatar, Button, Card, CardActions, CircularProgress, Stack } from "@mui/material";
import Box from "@mui/material/Box";
import { Fragment, useEffect, useState } from "react";
import { Form, TextInput, required, useLogin, useNotify, useTheme } from "react-admin";
import { useAuth } from "react-oidc-context";
import { Navigate, useLocation } from "react-router-dom";

import { jwt_signed_in } from "../../access_control/auth_provider/authProvider";
import { oidc_signed_in } from "../../access_control/auth_provider/oidc";
import { OIDCSignInButton } from "../auth_provider/OIDCSignInButton";
import { getTheme } from "../users/functions";

const Login = () => {
    const [loading, setLoading] = useState(false);
    const [, setTheme] = useTheme();
    const auth = useAuth();
    const [featureDisableUserLogin, setFeatureDisableUserLogin] = useState(false);
    const notify = useNotify();
    const login = useLogin();
    const location = useLocation();
    const [newLocation, setNewLocation] = useState("/");

    const isAuthenticated = jwt_signed_in() || oidc_signed_in();

    useEffect(() => {
        if (window.__RUNTIME_CONFIG__.OIDC_ENABLE == "true") {
            const settingsStorage = localStorage.getItem("settings");
            if (settingsStorage) {
                const settings = JSON.parse(settingsStorage);
                const features = settings.features || [];
                setFeatureDisableUserLogin(features.indexOf("feature_disable_user_login") !== -1);
            } else {
                get_disable_login_feature();
            }
        }
    }, []);

    function get_disable_login_feature() {
        const request = new Request(window.__RUNTIME_CONFIG__.API_BASE_URL + "/status/settings/", {
            method: "GET",
            headers: new Headers({
                "Content-Type": "application/json",
            }),
        });
        return fetch(request)
            .then((response) => {
                if (response.status < 200 || response.status >= 300) {
                    throw new Error(response.statusText);
                }
                return response.json();
            })
            .then((data) => {
                localStorage.setItem("settings", JSON.stringify(data));
                const features = data.features || [];
                const feature_disable_user_login_position = features.indexOf("feature_disable_user_login");
                setFeatureDisableUserLogin(feature_disable_user_login_position !== -1);
            });
    }

    interface FormValues {
        username?: string;
        password?: string;
    }

    const handleSubmit = async (auth: FormValues) => {
        setLoading(true);
        login(auth)
            .then(() => {
                setTheme(getTheme());
                setNewLocation("/");
                const last_location = localStorage.getItem("last_location");
                if (last_location) {
                    localStorage.removeItem("last_location");
                    if (last_location.startsWith("#")) {
                        setNewLocation(last_location.substring(1));
                    } else {
                        setNewLocation(last_location);
                    }
                }
            })
            .catch((error: Error) => {
                setLoading(false);
                notify(
                    typeof error === "string"
                        ? error
                        : typeof error === "undefined" || !error.message // eslint-disable-line @typescript-eslint/prefer-optional-chain
                          ? "ra.auth.sign_in_error"
                          : error.message,
                    {
                        type: "warning",
                        messageArgs: {
                            _: typeof error === "string" ? error : error?.message ? error.message : undefined,
                        },
                    }
                );
            });

        setLoading(false);
    };

    function show_user_login() {
        return (
            window.__RUNTIME_CONFIG__.OIDC_ENABLE == "false" ||
            !featureDisableUserLogin ||
            location.hash == "#force_user_login"
        );
    }

    return (
        <Fragment>
            {isAuthenticated && <Navigate to={newLocation} replace={true} />}
            {!isAuthenticated && !auth.isLoading && (
                <Form onSubmit={handleSubmit} noValidate>
                    <Box
                        sx={{
                            display: "flex",
                            flexDirection: "column",
                            minHeight: "100vh",
                            alignItems: "center",
                            justifyContent: "center",
                            background: "url(background_login.png)",
                            backgroundRepeat: "no-repeat",
                            backgroundSize: "cover",
                        }}
                    >
                        <Card sx={{ minWidth: 300 }}>
                            <Box
                                sx={{
                                    margin: "1em",
                                    display: "flex",
                                    justifyContent: "center",
                                }}
                            >
                                <Avatar sx={{ bgcolor: "primary.main" }}>
                                    <LockIcon />
                                </Avatar>
                            </Box>
                            {show_user_login() && (
                                <Box sx={{ padding: "0 1em 1em 1em" }}>
                                    <Box sx={{ marginTop: "1em" }}>
                                        <TextInput
                                            autoFocus
                                            source="username"
                                            label="Username"
                                            disabled={loading}
                                            validate={required()}
                                            fullWidth
                                        />
                                    </Box>
                                    <Box sx={{ marginTop: "1em" }}>
                                        <TextInput
                                            source="password"
                                            label="Password"
                                            type="password"
                                            disabled={loading}
                                            validate={required()}
                                            fullWidth
                                        />
                                    </Box>
                                </Box>
                            )}
                            <CardActions sx={{ padding: "0 1em 1em 1em" }}>
                                <Stack spacing={2} sx={{ width: "100%" }}>
                                    {show_user_login() && (
                                        <Button
                                            variant="contained"
                                            type="submit"
                                            color="primary"
                                            disabled={loading}
                                            fullWidth
                                            startIcon={<PersonIcon />}
                                        >
                                            {loading && <CircularProgress size={25} thickness={2} />}
                                            Sign in with user
                                        </Button>
                                    )}
                                    {window.__RUNTIME_CONFIG__.OIDC_ENABLE == "true" && <OIDCSignInButton />}
                                </Stack>
                            </CardActions>
                        </Card>
                    </Box>
                </Form>
            )}
        </Fragment>
    );
};

export default Login;
