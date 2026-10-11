export function getServerTimeZone(): string {
    try {
        const time_zone = JSON.parse(localStorage.getItem("settings") ?? "{}").time_zone;
        if (time_zone) {
            // Throws a RangeError if the browser does not know the time zone
            new Intl.DateTimeFormat(undefined, { timeZone: time_zone });
            return time_zone;
        }
    } catch {
        // fall back to the time zone of the browser
    }
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

/** Calendar date in the server time zone, e.g. "2026-10-03" */
export function getServerDate(date: Date): string {
    const parts = new Intl.DateTimeFormat("en-US", {
        timeZone: getServerTimeZone(),
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
    }).formatToParts(date);
    const part = (type: string) => parts.find((p) => p.type === type)?.value;
    return `${part("year")}-${part("month")}-${part("day")}`;
}
