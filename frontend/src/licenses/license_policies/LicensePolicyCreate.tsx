import { Typography } from "@mui/material";
import { useState } from "react";
import { AutocompleteArrayInput, BooleanInput, Create, ReferenceInput, SimpleForm } from "react-admin";

import license_policies from ".";
import MarkdownEdit from "../../commons/custom_fields/MarkdownEdit";
import { validate_255, validate_required_255 } from "../../commons/custom_validators";
import { AutocompleteInputWide, TextInputWide } from "../../commons/layout/themes";
import { PURL_TYPE_CHOICES } from "../../core/types";

const LicensePolicyCreate = () => {
    const [description, setDescription] = useState("");
    const transform = (data: any) => {
        data.description = description;
        data.ignore_component_types ??= "";
        return data;
    };

    return (
        <Create redirect="show" transform={transform}>
            <SimpleForm warnWhenUnsavedChanges>
                <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                    <license_policies.icon />
                    &nbsp;&nbsp;License Policy
                </Typography>
                <TextInputWide autoFocus source="name" validate={validate_required_255} />
                <MarkdownEdit initialValue="" setValue={setDescription} label="Description" maxLength={2048} />
                <ReferenceInput
                    source="parent"
                    reference="license_policies"
                    filter={{ is_child: false }}
                    sort={{ field: "name", order: "ASC" }}
                >
                    <AutocompleteInputWide optionText="name" />
                </ReferenceInput>
                <AutocompleteArrayInput
                    source="ignore_component_type_list"
                    choices={PURL_TYPE_CHOICES}
                    validate={validate_255}
                    sx={{ width: "30em" }}
                />
                <BooleanInput source="is_public" label="Public" />
            </SimpleForm>
        </Create>
    );
};

export default LicensePolicyCreate;
