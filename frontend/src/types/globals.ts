export {};

declare global {
    interface Window {
        __RUNTIME_CONFIG__: {
            API_BASE_URL: string;
            OIDC_ENABLE: string;
            OIDC_AUTHORITY: string;
            OIDC_CLIENT_ID: string;
            OIDC_REDIRECT_URI: string;
            OIDC_POST_LOGOUT_REDIRECT_URI: string;
            OIDC_SCOPE: string;
            OIDC_PROMPT: string;
        };
    }
}
