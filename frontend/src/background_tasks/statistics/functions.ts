export function formatDuration(seconds: number): string {
    if (seconds < 1) {
        return `${Math.round(seconds * 1000)} ms`;
    }
    if (seconds < 60) {
        return `${seconds.toFixed(1)} s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remaining_seconds = Math.round(seconds % 60);
    return `${minutes} min ${remaining_seconds} s`;
}
