import { Labeled, ReferenceField, ReferenceInput, TextField } from "react-admin";

import { AutocompleteInputWide } from "../../../commons/layout/themes";

export const LicenseManagementInputs = () => (
    <ReferenceInput
        source="license_policy"
        reference="license_policies"
        label="License policy"
        sort={{ field: "name", order: "ASC" }}
    >
        <AutocompleteInputWide optionText="name" />
    </ReferenceInput>
);

export const isLicenseManagementVisible = (product: any) => Boolean(product.license_policy);

export const LicenseManagementFields = () => (
    <Labeled label="License policy">
        <ReferenceField
            source="license_policy"
            reference="license_policies"
            link="show"
            sx={{ "& a": { textDecoration: "none" } }}
        >
            <TextField source="name" />
        </ReferenceField>
    </Labeled>
);
