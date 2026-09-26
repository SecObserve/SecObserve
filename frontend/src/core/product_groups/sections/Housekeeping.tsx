import { Stack } from "@mui/material";
import {
    BooleanField,
    FormDataConsumer,
    Labeled,
    NullableBooleanInput,
    NumberField,
    NumberInput,
    TextField,
    useRecordContext,
} from "react-admin";

import { validate_0_999999, validate_255 } from "../../../commons/custom_validators";
import { TextInputWide } from "../../../commons/layout/themes";

export const HousekeepingInputs = () => (
    <>
        <NullableBooleanInput
            source="repository_branch_housekeeping_active"
            label="Housekeeping"
            defaultValue={null}
            nullLabel="Standard"
            falseLabel="Disabled"
            trueLabel="Product group specific"
            helperText="Delete inactive branches / versions"
        />
        <FormDataConsumer>
            {({ formData }) =>
                formData.repository_branch_housekeeping_active && (
                    <Stack spacing={2}>
                        <NumberInput
                            source="repository_branch_housekeeping_keep_inactive_days"
                            label="Keep inactive"
                            helperText="Days before inactive branches / versions and their observations are deleted"
                            defaultValue={30}
                            min={1}
                            max={999999}
                            validate={validate_0_999999}
                        />
                        <TextInputWide
                            source="repository_branch_housekeeping_exempt_branches"
                            label="Exempt branches / versions"
                            helperText="Regular expression which branches / versions to exempt from deletion"
                            validate={validate_255}
                        />
                    </Stack>
                )
            }
        </FormDataConsumer>
    </>
);

export const isHousekeepingVisible = (product_group: any) =>
    product_group.repository_branch_housekeeping_active != null;

export const HousekeepingFields = () => {
    const product_group: any = useRecordContext();
    if (!product_group) {
        return null;
    }

    return (
        <Stack direction="row" spacing={4} sx={{ marginTop: 1 }}>
            <Labeled label="Housekeeping">
                <BooleanField
                    source="repository_branch_housekeeping_active"
                    valueLabelFalse="Disabled"
                    valueLabelTrue="Product group specific"
                />
            </Labeled>
            {product_group.repository_branch_housekeeping_active &&
                product_group.repository_branch_housekeeping_keep_inactive_days && (
                    <Labeled label="Keep inactive">
                        <NumberField source="repository_branch_housekeeping_keep_inactive_days" />
                    </Labeled>
                )}
            {product_group.repository_branch_housekeeping_active &&
                product_group.repository_branch_housekeeping_exempt_branches && (
                    <Labeled label="Exempt branches / versions">
                        <TextField source="repository_branch_housekeeping_exempt_branches" />
                    </Labeled>
                )}
        </Stack>
    );
};
