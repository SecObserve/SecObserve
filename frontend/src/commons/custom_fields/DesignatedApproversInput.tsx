import { Stack, Typography } from "@mui/material";
import { Identifier, RaRecord, useGetList, useRecordContext } from "react-admin";

import { ROLE_CHOICES } from "../../access_control/types";
import { AutocompleteArrayInputWide } from "../layout/themes";

// Approval-capable role ids: Writer (3), Maintainer (4), Owner (5).
const APPROVAL_CAPABLE_ROLE_IDS = new Set([3, 4, 5]);

interface UserRecord extends RaRecord {
    full_name: string;
    product_role: number | null;
}

// Renders the option row inside the autocomplete dropdown: full name on top, role label below.
const ApproverOptionItem = () => {
    const record = useRecordContext<UserRecord>();
    if (!record) return null;
    const role = ROLE_CHOICES.find((r) => r.id === record.product_role);
    return (
        <Stack>
            <Typography variant="body2">{record.full_name}</Typography>
            <Typography variant="caption" color="text.secondary">
                {role ? role.name : ""}
            </Typography>
        </Stack>
    );
};

interface DesignatedApproversInputProps {
    approver_filter: { member_of_product: Identifier };
    helperText: string;
}

export const DesignatedApproversInput = ({ approver_filter, helperText }: DesignatedApproversInputProps) => {
    // Fetch members directly so we can filter to approval-capable roles client-side. Using ReferenceArrayInput
    // has no built-in choice filter, so useGetList is the cleanest approach for the filtering requirement.
    const { data } = useGetList<UserRecord>("users", {
        filter: approver_filter,
        sort: { field: "full_name", order: "ASC" },
        pagination: { page: 1, perPage: 100 },
    });

    const choices = (data ?? []).filter(
        (u) => u.product_role !== null && APPROVAL_CAPABLE_ROLE_IDS.has(u.product_role)
    );

    return (
        <AutocompleteArrayInputWide
            source="assessment_approvers"
            label="Designated approvers"
            helperText={helperText}
            choices={choices}
            optionText={<ApproverOptionItem />}
            inputText={(record: RaRecord) => (record as UserRecord).full_name}
            matchSuggestion={(filterValue: string, record: RaRecord) =>
                (record as UserRecord).full_name.toLowerCase().includes(filterValue.toLowerCase())
            }
        />
    );
};
