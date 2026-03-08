import { Identifier, RaRecord } from "react-admin";

export const TYPE_CHOICES = [
    { id: "Exception", name: "Exception" },
    { id: "Observation", name: "Observation" },
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
    function: string;
    arguments: string;
}
