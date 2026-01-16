import { UserManager } from "oidc-client-ts";
import { AuthProvider } from "react-admin";

import { set_settings_in_local_storage } from "../../commons/functions";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { oidcConfig, oidcStorageKey, oidc_signed_in } from "./oidc";

const authProvider: AuthProvider = {
    login: async ({ username, password }) => {
        if (oidc_signed_in()) {
            return Promise.resolve();
        } else {
            const request = new Request(window.__RUNTIME_CONFIG__.API_BASE_URL + "/authentication/authenticate/", {
                method: "POST",
                body: JSON.stringify({ username, password }),
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
                .then((response) => {
                    localStorage.setItem("jwt", response.jwt);
                    localStorage.setItem("user", JSON.stringify(response.user));
                    localStorage.setItem("theme", response.user.setting_theme);
                })
                .catch((error) => {
                    if (error.message == "Forbidden") {
                        throw new Error("Invalid credentials");
                    } else {
                        throw new Error("Network error");
                    }
                });
        }
    },
    logout: async () => {
        localStorage.removeItem("jwt");
        localStorage.removeItem("user");
        localStorage.removeItem("notification_count");

        if (oidc_signed_in()) {
            const user_manager = new UserManager(oidcConfig);
            return user_manager.signoutRedirect();
        }

        return Promise.resolve();
    },
    checkError: async (error) => {
        if (error.status === 401) {
            if (location.hash !== "#/login") {
                localStorage.setItem("last_location", location.hash);
            }
            if (oidc_signed_in()) {
                const user_manager = new UserManager(oidcConfig);
                localStorage.removeItem(oidcStorageKey);
                return user_manager.signinRedirect();
            }
            throw error;
        }
    },
    checkAuth: () => {
        if (oidc_signed_in() || jwt_signed_in()) {
            return Promise.resolve();
        }

        if (location.hash != "" && !location.hash.startsWith("#/login")) {
            localStorage.setItem("last_location", location.hash);
        }

        return Promise.reject({ message: false });
    },
    getPermissions: () => Promise.reject(),
    getIdentity: async () => {
        const id = 0;
        let fullName = "";
        const avatar = undefined;

        let user = localStorage.getItem("user");
        if (!user) {
            await setUserInfo();
        }
        user = localStorage.getItem("user");
        if (user) {
            const user_json = JSON.parse(user);
            fullName = user_json.full_name;
        }

        set_settings_in_local_storage();

        return Promise.resolve({ id, fullName, avatar });
    },
};

export const setUserInfo = async () => {
    const userinfo = await getUserInfo();
    localStorage.setItem("user", JSON.stringify(userinfo));
    localStorage.setItem("theme", userinfo.setting_theme);
};

const getUserInfo = () => {
    return httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/users/me/").then((response) => {
        return response.json;
    });
};

export function jwt_signed_in(): boolean {
    return localStorage.getItem("jwt") != null;
}

export default authProvider;
