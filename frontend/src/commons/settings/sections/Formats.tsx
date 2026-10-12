import { Grid } from "@mui/material";
import { FunctionField, Labeled, RadioButtonGroupInput, useRecordContext } from "react-admin";

import { DATE_FORMAT_CHOICES } from "../../types";

export const FormatsInputs = () => (
    <Grid container spacing={2} sx={{ width: "100%" }}>
        <Grid size={4}>
            <RadioButtonGroupInput
                source="date_format"
                label="Date format"
                choices={DATE_FORMAT_CHOICES}
                helperText="Format to display dates and times in the frontend, a reload of the page is needed to apply a change"
                sx={{ marginBottom: 2 }}
            />
        </Grid>
    </Grid>
);

export const FormatsFields = () => {
    const settings: any = useRecordContext();
    if (!settings) {
        return null;
    }

    return (
        <Grid container spacing={2} sx={{ width: "100%", marginBottom: 2 }}>
            <Grid size={4}>
                <Labeled label="Date format">
                    <FunctionField
                        render={(record: any) =>
                            DATE_FORMAT_CHOICES.find((choice) => choice.id === record.date_format)?.name ??
                            record.date_format
                        }
                    />
                </Labeled>
            </Grid>
        </Grid>
    );
};
