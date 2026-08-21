import { Identifier, RaRecord, useGetList } from "react-admin";

import { getUserOptionText } from "../functions";
import { AutocompleteArrayInputWide } from "../layout/themes";

interface UserRecord extends RaRecord {
    full_name: string;
    username: string;
}

interface DesignatedApproversInputProps {
    approver_filter: { assessment_approver_for_product: Identifier };
    helperText: string;
}

export const DesignatedApproversInput = ({ approver_filter, helperText }: DesignatedApproversInputProps) => {
    const { data } = useGetList<UserRecord>("users", {
        filter: approver_filter,
        sort: { field: "full_name", order: "ASC" },
        pagination: { page: 1, perPage: 100 },
    });

    return (
        <AutocompleteArrayInputWide
            source="assessment_approvers"
            label="Designated approvers"
            helperText={helperText}
            choices={data ?? []}
            optionText={getUserOptionText}
            inputText={(record: RaRecord) => getUserOptionText(record)}
            matchSuggestion={(filterValue: string, record: RaRecord) => {
                const user = record as UserRecord;
                return (
                    user.full_name.toLowerCase().includes(filterValue.toLowerCase()) ||
                    (user.username ?? "").toLowerCase().includes(filterValue.toLowerCase())
                );
            }}
        />
    );
};
