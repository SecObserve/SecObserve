export const PERIODIC_TASKS_STATUS_CHOICES = [
    { id: "Success", name: "Success" },
    { id: "Failure", name: "Failure" },
    { id: "Running", name: "Running" },
];

export interface BackgroundTaskBreakdown {
    task: string;
    full: string;
    executed: number;
    completed: number;
    errors: number;
    retries: number;
    avg: number | null;
}

export interface BackgroundTaskThroughput {
    complete: number[];
    error: number[];
}

export interface BackgroundTaskRunning {
    task: string;
    id: string;
    started: number;
    elapsed: number;
}

export interface BackgroundTaskCounts {
    enqueued: number;
    scheduled: number;
    executing: number;
    complete: number;
    error: number;
    retrying: number;
    revoked: number;
    canceled: number;
    expired: number;
    locked: number;
    interrupted: number;
}

export interface BackgroundTaskStatistics {
    registered: BackgroundTaskBreakdown[];
    throughput: BackgroundTaskThroughput;
    counts: BackgroundTaskCounts;
    running: BackgroundTaskRunning[];
}
