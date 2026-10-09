import { User, UserManager, WebStorageStateStore } from "oidc-client-ts";
import { HttpError } from "react-admin";

/** Tokens are renewed when they expire within this time. */
const REFRESH_MARGIN_SECONDS = 60;
const REFRESH_LOCK_NAME = "secobserve-oidc-refresh";

const oidcConfig = {
    userStore: new WebStorageStateStore({ store: window.localStorage }),
    authority: window.__RUNTIME_CONFIG__.OIDC_AUTHORITY,
    client_id: window.__RUNTIME_CONFIG__.OIDC_CLIENT_ID,
    redirect_uri: window.__RUNTIME_CONFIG__.OIDC_REDIRECT_URI,
    post_logout_redirect_uri: window.__RUNTIME_CONFIG__.OIDC_POST_LOGOUT_REDIRECT_URI,
    scope:
        window.__RUNTIME_CONFIG__.OIDC_SCOPE && window.__RUNTIME_CONFIG__.OIDC_SCOPE !== "dummy"
            ? window.__RUNTIME_CONFIG__.OIDC_SCOPE
            : "openid profile email",
    // The library's automatic renewal would run independently of the renewals before API calls.
    // With refresh token rotation, concurrent renewals with the same refresh token fail,
    // so all renewals go through refresh_oidc_token().
    automaticSilentRenew: false,
    accessTokenExpiringNotificationTimeInSeconds: REFRESH_MARGIN_SECONDS,
    ...(window.__RUNTIME_CONFIG__.OIDC_PROMPT && window.__RUNTIME_CONFIG__.OIDC_PROMPT !== ""
        ? { prompt: window.__RUNTIME_CONFIG__.OIDC_PROMPT }
        : {}),
};

/** The only UserManager of the application, every instance would keep its own timers and state. */
export const userManager = new UserManager(oidcConfig);

userManager.events.addAccessTokenExpiring(() => {
    refresh_oidc_token().catch((error: Error) => {
        // The renewal is tried again before the next API call
        console.warn("OIDC token renewal failed:", error);
    });
});

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const onSigninCallback = (_user: User | void): void => {
    userManager.clearStaleState();
    const last_location = localStorage.getItem("last_location");
    if (last_location) {
        localStorage.removeItem("last_location");
        location.hash = last_location;
        window.location.replace("/" + last_location);
    } else {
        window.history.replaceState({}, document.title, window.location.pathname);
    }
};

export const oidcStorageKey =
    "oidc.user:" + window.__RUNTIME_CONFIG__.OIDC_AUTHORITY + ":" + window.__RUNTIME_CONFIG__.OIDC_CLIENT_ID;

export function oidcStorageUser(): string | null {
    return localStorage.getItem(oidcStorageKey);
}

export function oidc_signed_in(): boolean {
    return oidcStorageUser() != null;
}

function get_oidc_user(): User | null {
    const storage_user = oidcStorageUser();
    return storage_user ? User.fromStorageString(storage_user) : null;
}

export function get_oidc_id_token(): string | null {
    return get_oidc_user()?.id_token ?? null;
}

function get_jwt_expiry(token: string): number | null {
    try {
        const payload = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
        const claims = JSON.parse(atob(payload));
        return typeof claims.exp === "number" ? claims.exp : null;
    } catch {
        return null;
    }
}

/** The backend authenticates with the id token, so its expiry is checked as well as the access token's. */
function token_expires_within(user: User, seconds: number): boolean {
    const limit = Date.now() / 1000 + seconds;
    const id_token_expiry = user.id_token ? get_jwt_expiry(user.id_token) : null;
    if (id_token_expiry === null || id_token_expiry <= limit) {
        return true;
    }
    return user.expires_at !== undefined && user.expires_at <= limit;
}

function with_refresh_lock(callback: () => Promise<void>): Promise<void> {
    // Web Locks are only available in secure contexts
    if ("locks" in navigator) {
        return navigator.locks.request(REFRESH_LOCK_NAME, callback);
    }
    return callback();
}

async function refresh_if_needed(rejected_id_token: string | null | undefined): Promise<void> {
    const user = get_oidc_user();
    if (!user) {
        return;
    }
    const already_refreshed =
        rejected_id_token === undefined
            ? !token_expires_within(user, REFRESH_MARGIN_SECONDS)
            : user.id_token !== rejected_id_token;
    if (already_refreshed) {
        // Another browser tab has renewed the token in the meantime, the in-memory state is synchronized
        await userManager.getUser();
        return;
    }

    const refreshed_user = await userManager.signinSilent();
    if (!refreshed_user || token_expires_within(refreshed_user, REFRESH_MARGIN_SECONDS)) {
        console.warn(
            "OIDC token renewal did not provide a new id token. " +
                "The OIDC provider needs to return an id token when the refresh token is used."
        );
        throw new Error("OIDC token renewal did not provide a new id token");
    }
}

let refresh_in_flight: Promise<void> | null = null;

/**
 * Renews the OIDC tokens. Concurrent calls in this and in other browser tabs share one renewal,
 * because providers with refresh token rotation reject a refresh token that has already been used.
 *
 * @param rejected_id_token If given, the tokens are renewed when the stored id token is still this one,
 *     otherwise when the stored tokens are about to expire.
 */
export function refresh_oidc_token(rejected_id_token?: string | null): Promise<void> {
    refresh_in_flight ??= with_refresh_lock(() => refresh_if_needed(rejected_id_token)).finally(() => {
        refresh_in_flight = null;
    });
    return refresh_in_flight;
}

/** Sends the user to the OIDC provider to authenticate again.
 *
 * `prompt=login` forces the authentication, `max_age=0` makes the `auth_time` claim
 * mandatory in the id token, which the backend needs to check the age of the authentication.
 */
export function oidc_reauthenticate(
    signinRedirect: (args: { prompt: string; max_age: number }) => Promise<void>
): Promise<void> {
    if (location.hash !== "#/login") {
        localStorage.setItem("last_location", location.hash);
    }
    return signinRedirect({ prompt: "login", max_age: 0 });
}

let signin_redirect: Promise<void> | null = null;

async function start_signin_redirect(): Promise<void> {
    if (location.hash !== "#/login") {
        localStorage.setItem("last_location", location.hash);
    }
    await userManager.removeUser();
    // The promise only settles when the browser shows this page again from its cache,
    // after the user has navigated back from the OIDC provider without signing in.
    await userManager.signinRedirect();
    throw new Error("Sign-in has been aborted");
}

/**
 * Sends the user to the OIDC provider to sign in again, instead of logging out.
 * With an active session at the OIDC provider, the user gets back without any input.
 * Concurrent calls share one redirect.
 */
export function oidc_signin_again(): Promise<void> {
    signin_redirect ??= start_signin_redirect().finally(() => {
        signin_redirect = null;
    });
    return signin_redirect;
}

export const updateRefreshToken = async (): Promise<void> => {
    const user = get_oidc_user();
    if (!user || !token_expires_within(user, REFRESH_MARGIN_SECONDS)) {
        return;
    }
    try {
        await refresh_oidc_token();
    } catch (error) {
        if (!token_expires_within(user, 0)) {
            // The current token is still valid and can be used, the renewal is tried again with the next call
            console.warn("OIDC token renewal failed:", error);
            return;
        }
        if (!navigator.onLine) {
            // A redirect would only show an error page, the renewal is tried again with the next call
            throw error;
        }
        console.warn("OIDC token renewal failed, signing in again:", error);
        return oidc_signin_again();
    }
};

/**
 * Executes an API request with the OIDC id token. If the backend rejects the token,
 * the tokens are renewed and the request is executed once more.
 */
export async function oidc_request_with_retry<T>(request: () => Promise<T>): Promise<T> {
    await updateRefreshToken();
    const id_token = get_oidc_id_token();
    try {
        return await request();
    } catch (error) {
        if (!(error instanceof HttpError) || error.status !== 401) {
            throw error;
        }
        try {
            await refresh_oidc_token(id_token);
        } catch {
            throw error;
        }
        return request();
    }
}
