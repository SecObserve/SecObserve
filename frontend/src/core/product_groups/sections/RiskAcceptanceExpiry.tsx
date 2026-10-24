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
    <>
        <NullableBooleanInput
            source="risk_acceptance_expiry_active"
            label="Risk acceptance expiry"
            defaultValue={null}
            nullLabel="Standard"
            falseLabel="Disabled"
            trueLabel="Product group specific"
            helperText="Set date for expiry or risk acceptance"
            sx={{ width: "15em", marginBottom: 2 }}
        />
        <FormDataConsumer>
            {({ formData }) =>
                formData.risk_acceptance_expiry_active && (
                    <Stack spacing={2}>
                        <NumberInput
                            source="risk_acceptance_expiry_days"
                            label="Risk acceptance expiry (days)"
                            helperText="Days after which the risk acceptance expires"
                            defaultValue={30}
                            min={1}
                            max={999999}
                            validate={validate_0_999999}
                        />
                    </Stack>
                )
            }
        </FormDataConsumer>
        <NullableBooleanInput
            source="not_affected_expiry_active"
            label="Not affected expiry"
            defaultValue={null}
            nullLabel="Standard"
            falseLabel="Disabled"
            trueLabel="Product group specific"
            helperText="Set date for expiry of Not affected assessments"
            sx={{ width: "15em", marginBottom: 2 }}
        />
        <FormDataConsumer>
            {({ formData }) =>
                formData.not_affected_expiry_active && (
                    <Stack spacing={2}>
                        <NumberInput
                            source="not_affected_expiry_days"
                            label="Not affected expiry (days)"
                            helperText="Days after which a Not affected assessment expires"
                            defaultValue={30}
                            min={1}
                            max={999999}
                            validate={validate_0_999999}
                        />
                    </Stack>
                )
            }
        </FormDataConsumer>
    </>
);

export const isRiskAcceptanceExpiryVisible = (product_group: any) =>
    product_group.risk_acceptance_expiry_active != null || product_group.not_affected_expiry_active != null;

export const RiskAcceptanceExpiryFields = () => {
    const product_group: any = useRecordContext();
    if (!product_group) {
        return null;
    }

    return (
        <>
            {product_group.risk_acceptance_expiry_active != null && (
                <Labeled label="Risk acceptance expiry">
                    <BooleanField
                        source="risk_acceptance_expiry_active"
                        valueLabelFalse="Disabled"
                        valueLabelTrue="Product group specific"
                    />
                </Labeled>
            )}
            {product_group.risk_acceptance_expiry_active && (
                <Stack spacing={1}>
                    <Labeled label="Risk acceptance expiry (days)">
                        <NumberField source="risk_acceptance_expiry_days" />
                    </Labeled>
                </Stack>
            )}
            {product_group.not_affected_expiry_active != null && (
                <Labeled label="Not affected expiry">
                    <BooleanField
                        source="not_affected_expiry_active"
                        valueLabelFalse="Disabled"
                        valueLabelTrue="Product group specific"
                    />
                </Labeled>
            )}
            {product_group.not_affected_expiry_active && (
                <Stack spacing={1}>
                    <Labeled label="Not affected expiry (days)">
                        <NumberField source="not_affected_expiry_days" />
                    </Labeled>
                </Stack>
            )}
        </>
    );
};
