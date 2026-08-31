import { HttpError } from "react-admin";

import { jwt_signed_in } from "../../access_control/auth_provider/authProvider";
import { get_oidc_id_token, oidc_signed_in } from "../../access_control/auth_provider/oidc";

const base_url = window.__RUNTIME_CONFIG__.API_BASE_URL;

function authorization_header(): Record<string, string> {
    if (oidc_signed_in()) {
        return { Authorization: "Bearer " + get_oidc_id_token() };
    }
    if (jwt_signed_in()) {
        return { Authorization: "JWT " + localStorage.getItem("jwt") };
    }
    return {};
}

function full_url(url: string): string {
    return base_url + (url.startsWith("/") ? "" : "/") + url;
}

function parse_json(body: string): any {
    try {
        return JSON.parse(body);
    } catch {
        return undefined;
    }
}

async function fetch_instance(url: string, options: RequestInit): Promise<Response> {
    const response = await fetch(full_url(url), {
        ...options,
        headers: { ...authorization_header(), ...options.headers },
    });

    if (!response.ok) {
        const body = await response.text();
        const json = parse_json(body);
        throw new HttpError(json?.message ?? response.statusText, response.status, json ?? body);
    }

    return response;
}

export function fetch_get(url: string): Promise<Response> {
    return fetch_instance(url, { method: "GET" });
}

export function fetch_post(url: string, data: any): Promise<Response> {
    return fetch_instance(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });
}
