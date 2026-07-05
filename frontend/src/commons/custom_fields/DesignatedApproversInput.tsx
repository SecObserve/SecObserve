import { Identifier, RaRecord, useGetList } from "react-admin";

import { AutocompleteArrayInputWide } from "../layout/themes";

interface UserRecord extends RaRecord {
    full_name: string;
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
            optionText="full_name"
            inputText={(record: RaRecord) => (record as UserRecord).full_name}
            matchSuggestion={(filterValue: string, record: RaRecord) =>
                (record as UserRecord).full_name.toLowerCase().includes(filterValue.toLowerCase())
            }
        />
    );
};
