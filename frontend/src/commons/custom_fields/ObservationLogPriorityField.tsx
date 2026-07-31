import { Typography } from "@mui/material";
import { NumberField, useRecordContext } from "react-admin";

interface ObservationLogPriorityFieldProps {
    source: string;
    label?: string;
    sortable?: boolean;
}

export const ObservationLogPriorityField = (props: ObservationLogPriorityFieldProps) => {
    const record = useRecordContext();

    if (!record) {
        return null;
    }

    if (!record.priority_changed) {
        return (
            <Typography component="span" variant="body2">
                ---
            </Typography>
        );
    }

    return <NumberField source={props.source} sortable={props.sortable} emptyText="None" />;
};
