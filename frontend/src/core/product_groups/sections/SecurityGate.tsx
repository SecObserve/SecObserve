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
            trueLabel="Product group specific"
            label="Security gate"
            helperText="Shows that a product does not exceed a defined amount of vulnerabilities per severity"
            sx={{ marginBottom: 2 }}
        />
        <FormDataConsumer>
            {({ formData }) => formData.security_gate_active && <SecurityGateThresholdsInputs />}
        </FormDataConsumer>
    </>
);

export const isSecurityGateVisible = (product_group: any) => product_group.security_gate_active != null;

export const SecurityGateFields = () => {
    const product_group: any = useRecordContext();
    if (!product_group) {
        return null;
    }

    return (
        <>
            <Labeled label="Security gate" sx={{ marginBottom: 2 }}>
                <BooleanField
                    source="security_gate_active"
                    valueLabelFalse="Disabled"
                    valueLabelTrue="Product group specific"
                />
            </Labeled>
            {product_group.security_gate_active && <SecurityGateThresholdsFields />}
        </>
    );
};
