import { BooleanField, BooleanInput, FormDataConsumer, Labeled, useRecordContext } from "react-admin";

import { SecurityGateThresholdsFields, SecurityGateThresholdsInputs } from "../../security_gate/SecurityGateThresholds";

export const SecurityGatesInputs = () => (
    <>
        <BooleanInput
            source="security_gate_active"
            label="Security gates active"
            helperText="Are security gates activated?"
            sx={{ marginBottom: 2 }}
        />
        <FormDataConsumer>
            {({ formData }) => formData.security_gate_active && <SecurityGateThresholdsInputs />}
        </FormDataConsumer>
    </>
);

export const SecurityGatesFields = () => {
    const settings: any = useRecordContext();
    if (!settings) {
        return null;
    }

    return (
        <>
            <Labeled label="Security gates active" sx={{ marginBottom: 2 }}>
                <BooleanField source="security_gate_active" />
            </Labeled>
            {settings.security_gate_active && <SecurityGateThresholdsFields />}
        </>
    );
};
