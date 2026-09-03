import { Identifier, RaRecord } from "react-admin";

export const TYPE_CHOICES = [
    { id: "Assessment request", name: "Assessment request" },
    { id: "Assessment result", name: "Assessment result" },
    { id: "Exception", name: "Exception" },
    { id: "Observation", name: "Observation" },
    { id: "Observation title", name: "Observation title" },
    { id: "Security gate", name: "Security gate" },
    { id: "Task", name: "Task" },
];

export interface Notification extends RaRecord {
    id: Identifier;
    type: string;
    name: string;
    created: Date;
    message: string;
    user: Identifier;
    observation: Identifier;
    observation_log?: Identifier;
    function: string;
    arguments: string;
}
