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

export const SecurityGateInputs = () => (
    <>
        <NullableBooleanInput
            source="security_gate_active"
            defaultValue={null}
            nullLabel="Standard"
            falseLabel="Disabled"
            trueLabel="Product specific"
            label="Security gate"
            helperText="Shows that the product does not exceed a defined amount of vulnerabilities per severity"
        />
        <FormDataConsumer>
            {({ formData }) =>
                formData.security_gate_active && (
                    <Stack spacing={1}>
                        <NumberInput
                            label="Threshold critical"
                            source="security_gate_threshold_critical"
                            min={0}
                            max={999999}
                            sx={{ width: "12em" }}
                            validate={validate_0_999999}
                        />
                        <NumberInput
                            label="Threshold high"
                            source="security_gate_threshold_high"
                            min={0}
                            max={999999}
                            sx={{ width: "12em" }}
                            validate={validate_0_999999}
                        />
                        <NumberInput
                            label="Threshold medium"
                            source="security_gate_threshold_medium"
                            min={0}
                            max={999999}
                            sx={{ width: "12em" }}
                            validate={validate_0_999999}
                        />
                        <NumberInput
                            label="Threshold low"
                            source="security_gate_threshold_low"
                            min={0}
                            max={999999}
                            sx={{ width: "12em" }}
                            validate={validate_0_999999}
                        />
                        <NumberInput
                            label="Threshold none"
                            source="security_gate_threshold_none"
                            min={0}
                            max={999999}
                            sx={{ width: "12em" }}
                            validate={validate_0_999999}
                        />
                        <NumberInput
                            label="Threshold unknown"
                            source="security_gate_threshold_unknown"
                            min={0}
                            max={999999}
                            sx={{ width: "12em" }}
                            validate={validate_0_999999}
                        />
                    </Stack>
                )
            }
        </FormDataConsumer>
    </>
);

export const isSecurityGateVisible = (product: any) =>
    Boolean(
        (!product.product_group && product.security_gate_active != null) ||
        (product.product_group &&
            product.product_group_security_gate_active == null &&
            product.security_gate_active != null)
    );

export const SecurityGateFields = () => {
    const product: any = useRecordContext();
    if (!product) {
        return null;
    }

    return (
        <>
            <Labeled label="Security gate">
                <BooleanField
                    source="security_gate_active"
                    valueLabelFalse="Disabled"
                    valueLabelTrue="Product specific"
                />
            </Labeled>
            {product.security_gate_active && (
                <Stack spacing={1}>
                    <Labeled>
                        <NumberField source="security_gate_threshold_critical" />
                    </Labeled>
                    <Labeled>
                        <NumberField source="security_gate_threshold_high" />
                    </Labeled>
                    <Labeled>
                        <NumberField source="security_gate_threshold_medium" />
                    </Labeled>
                    <Labeled>
                        <NumberField source="security_gate_threshold_low" />
                    </Labeled>
                    <Labeled>
                        <NumberField source="security_gate_threshold_none" />
                    </Labeled>
                    <Labeled>
                        <NumberField source="security_gate_threshold_unknown" />
                    </Labeled>
                </Stack>
            )}
        </>
    );
};

export const isSecurityGateProductGroupVisible = (product: any) =>
    Boolean(product.product_group && product.product_group_security_gate_active != null);

/** The security gate inherited from the product group, shown instead of the product's own one. */
export const SecurityGateProductGroupFields = () => (
    <Labeled label="Security gate (from product group)">
        <BooleanField
            source="product_group_security_gate_active"
            valueLabelFalse="Disabled"
            valueLabelTrue="Product group specific"
        />
    </Labeled>
);
