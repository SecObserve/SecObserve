import { ChipField, useRecordContext } from "react-admin";

interface PeriodicTaskStatusFieldProps {
    label: string;
}

export const PeriodicTaskStatusField = ({ label }: PeriodicTaskStatusFieldProps) => {
    const record = useRecordContext();

    function get_status_color() {
        if (record?.status === "Success") {
            return "#00aa00";
        } else if (record?.status === "Failure") {
            return "#d4333f";
        } else if (record?.status === "Running") {
            return "#00B4F0";
        } else {
            return "#424242";
        }
    }

    function get_text_record() {
        if (record?.status) {
            return { text: record.status };
        } else {
            return { text: "Unknown" };
        }
    }

    return record?.status != null ? (
        <ChipField
            label={label}
            source="text"
            record={get_text_record()}
            sortable={true}
            sortBy="status"
            sx={{
                backgroundColor: get_status_color(),
                color: "white",
            }}
        />
    ) : null;
};
