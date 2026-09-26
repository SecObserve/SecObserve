import { BooleanField, BooleanInput, Labeled } from "react-admin";

export const RulesInputs = () => <BooleanInput source="apply_general_rules" defaultValue={true} />;

export const RulesFields = () => (
    <Labeled label="Apply general rules">
        <BooleanField source="apply_general_rules" />
    </Labeled>
);
