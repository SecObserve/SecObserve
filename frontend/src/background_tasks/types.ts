export const PERIODIC_TASKS_STATUS_CHOICES = [
    { id: "Success", name: "Success" },
    { id: "Failure", name: "Failure" },
    { id: "Running", name: "Running" },
];

export interface TimeLine {
    completed: number[];
    error: number[];
};