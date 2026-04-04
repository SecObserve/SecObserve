import { Typography } from "@mui/material";
import { Fragment, useState } from "react";
import {
    AutocompleteArrayInput,
    BooleanInput,
    DeleteButton,
    Edit,
    ReferenceInput,
    SaveButton,
    SimpleForm,
    Toolbar,
    WithRecord,
    useRecordContext,
} from "react-admin";

import license_policies from ".";
import MarkdownEdit from "../../commons/custom_fields/MarkdownEdit";
import { validate_255, validate_required_255 } from "../../commons/custom_validators";
import { AutocompleteInputWide, TextInputWide } from "../../commons/layout/themes";
import { PURL_TYPE_CHOICES } from "../../core/types";

const CustomToolbar = () => {
    return (
        <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
            <SaveButton alwaysEnable />
            <DeleteButton mutationMode="pessimistic" redirect="/license/license_policies" />
        </Toolbar>
    );
};

interface LicensePolicyEditFormProps {
    setDescription: (value: string) => void;
}

const LicensePolicyEditForm = ({ setDescription }: LicensePolicyEditFormProps) => {
    const license_policy = useRecordContext();
    const [descriptionSet, setDescriptionSet] = useState(false);

    if (!descriptionSet && license_policy) {
        setDescription(license_policy.description);
        setDescriptionSet(true);
    }

    return (
        <SimpleForm warnWhenUnsavedChanges toolbar={<CustomToolbar />}>
            <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                <license_policies.icon />
                &nbsp;&nbsp;License Policy
            </Typography>
            <TextInputWide autoFocus source="name" validate={validate_required_255} />
            <MarkdownEdit
                initialValue={license_policy ? license_policy.description : ""}
                setValue={setDescription}
                label="Description"
                maxLength={2048}
            />
            <WithRecord
                render={(license_policy) => (
                    <Fragment>
                        {!license_policy.is_parent && (
                            <ReferenceInput
                                source="parent"
                                reference="license_policies"
                                filter={{ is_child: false, is_not_id: license_policy.id }}
                                sort={{ field: "name", order: "ASC" }}
                            >
                                <AutocompleteInputWide optionText="name" />
                            </ReferenceInput>
                        )}
                    </Fragment>
                )}
            />
            <AutocompleteArrayInput
                source="ignore_component_type_list"
                choices={PURL_TYPE_CHOICES}
                validate={validate_255}
                sx={{ width: "30em" }}
            />
            <BooleanInput source="is_public" label="Public" />
        </SimpleForm>
    );
};
const LicensePolicyEdit = () => {
    const [description, setDescription] = useState("");

    const transform = (data: any) => {
        data.description = description;
        return data;
    };

    return (
        <Edit redirect="show" mutationMode="pessimistic" transform={transform}>
            <LicensePolicyEditForm setDescription={setDescription} />
        </Edit>
    );
};

export default LicensePolicyEdit;
