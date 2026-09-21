import { Grid } from "@mui/material";
import {
    BooleanField,
    BooleanInput,
    FormDataConsumer,
    Labeled,
    NumberField,
    NumberInput,
    TextField,
    useRecordContext,
} from "react-admin";

import { validate_0_999999, validate_255 } from "../../custom_validators";
import { TextInputWide } from "../../layout/themes";

/** The backend does not accept null for these fields, they have to be sent as an empty string. */
export const transformBranchHousekeeping = (data: any) => {
    data.branch_housekeeping_exempt_branches ??= "";
};

export const BranchHousekeepingInputs = () => (
    <>
        <BooleanInput
            source="branch_housekeeping_active"
            label="Branch housekeeping active"
            helperText="Delete inactive branches"
            sx={{ marginBottom: 2 }}
        />
        <FormDataConsumer>
            {({ formData }) =>
                formData.branch_housekeeping_active && (
                    <Grid container spacing={2} sx={{ width: "100%" }}>
                        <Grid size={3}>
                            <NumberInput
                                source="branch_housekeeping_keep_inactive_days"
                                label="Branch housekeeping keep inactive (days)"
                                min={0}
                                step={1}
                                validate={validate_0_999999}
                                helperText="Days before incative branches and their observations are deleted"
                                sx={{ marginBottom: 2 }}
                            />
                        </Grid>
                        <Grid size={3}>
                            <TextInputWide
                                source="branch_housekeeping_exempt_branches"
                                label="Branch housekeeping exempt branches"
                                validate={validate_255}
                                helperText="Regular expression which branches to exempt from deletion"
                                sx={{ marginBottom: 2 }}
                            />
                        </Grid>
                    </Grid>
                )
            }
        </FormDataConsumer>
    </>
);

export const BranchHousekeepingFields = () => {
    const settings: any = useRecordContext();
    if (!settings) {
        return null;
    }

    return (
        <>
            <Labeled label="Branch housekeeping active">
                <BooleanField source="branch_housekeeping_active" sx={{ marginBottom: 1 }} />
            </Labeled>
            {settings.branch_housekeeping_active && (
                <Grid container spacing={2} sx={{ width: "100%" }}>
                    <Grid size={3}>
                        <Labeled label="Branch housekeeping keep inactive (days)">
                            <NumberField source="branch_housekeeping_keep_inactive_days" />
                        </Labeled>
                    </Grid>
                    <Grid size={3}>
                        {settings.branch_housekeeping_exempt_branches && (
                            <Labeled label="Branch housekeeping exempt branches">
                                <TextField source="branch_housekeeping_exempt_branches" />
                            </Labeled>
                        )}
                    </Grid>
                </Grid>
            )}
        </>
    );
};
