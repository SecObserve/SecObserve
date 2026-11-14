import { BooleanField, FormDataConsumer, Labeled, NullableBooleanInput, useRecordContext } from "react-admin";

import {
    SecurityGateThresholdsFields,
    SecurityGateThresholdsInputs,
} from "../../../commons/security_gate/SecurityGateThresholds";

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
            sx={{ marginBottom: 2 }}
        />
        <FormDataConsumer>
            {({ formData }) => formData.security_gate_active && <SecurityGateThresholdsInputs />}
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
            <Labeled label="Security gate" sx={{ marginBottom: 2 }}>
                <BooleanField
                    source="security_gate_active"
                    valueLabelFalse="Disabled"
                    valueLabelTrue="Product specific"
                />
            </Labeled>
            {product.security_gate_active && <SecurityGateThresholdsFields />}
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
