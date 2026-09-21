import { Stack } from "@mui/material";
import {
    BooleanField,
    FormDataConsumer,
    Labeled,
    NullableBooleanInput,
    NumberField,
    NumberInput,
    useRecordContext,
} from "react-admin";

import { validate_0_999999 } from "../../../commons/custom_validators";

export const RiskAcceptanceExpiryInputs = () => (
    <Stack direction="row" spacing={4}>
        <NullableBooleanInput
            source="risk_acceptance_expiry_active"
            label="Risk acceptance expiry"
            defaultValue={null}
            nullLabel="Standard"
            falseLabel="Disabled"
            trueLabel="Product specific"
            helperText="Set date for expiry of risk acceptance"
            sx={{ width: "15em", marginBottom: 2 }}
        />
        <FormDataConsumer>
            {({ formData }) =>
                formData.risk_acceptance_expiry_active && (
                    <NumberInput
                        source="risk_acceptance_expiry_days"
                        label="Risk acceptance expiry (days)"
                        helperText="Days after which the risk acceptance expires"
                        defaultValue={30}
                        min={1}
                        max={999999}
                        validate={validate_0_999999}
                    />
                )
            }
        </FormDataConsumer>
    </Stack>
);

export const isRiskAcceptanceExpiryVisible = (product: any) => product.risk_acceptance_expiry_active != null;

export const RiskAcceptanceExpiryFields = () => {
    const product: any = useRecordContext();
    if (!product) {
        return null;
    }

    return (
        <Stack direction="row" spacing={4}>
            <Labeled label="Risk acceptance expiry">
                <BooleanField
                    source="risk_acceptance_expiry_active"
                    valueLabelFalse="Disabled"
                    valueLabelTrue="Product specific"
                />
            </Labeled>
            {product.risk_acceptance_expiry_active && (
                <Labeled label="Risk acceptance expiry (days)">
                    <NumberField source="risk_acceptance_expiry_days" />
                </Labeled>
            )}
        </Stack>
    );
};
