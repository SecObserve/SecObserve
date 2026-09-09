import { httpClient } from "../../commons/ra-data-django-rest-framework";

export async function update_notification_count() {
    const url =
        window.__RUNTIME_CONFIG__.API_BASE_URL + "/notifications/?exclude_already_viewed=true&page=1&page_size=1";
    httpClient(url, {
        method: "GET",
    })
        .then((result) => {
            const count = result.json.count;
            localStorage.setItem("notification_count", count);
        })
        .catch((error) => {
            console.warn("Cannot update notification count: ", error.message);
        });
}

export function get_notification_count() {
    return localStorage.getItem("notification_count") || "";
}
