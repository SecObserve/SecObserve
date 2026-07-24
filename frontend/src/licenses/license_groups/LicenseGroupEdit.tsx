import { Typography } from "@mui/material";
import { useState } from "react";
import { BooleanInput, DeleteButton, Edit, SaveButton, SimpleForm, Toolbar, useRecordContext } from "react-admin";

import license_groups from ".";
import MarkdownEdit from "../../commons/custom_fields/MarkdownEdit";
import { validate_required_255 } from "../../commons/custom_validators";
import { TextInputWide } from "../../commons/layout/themes";

const CustomToolbar = () => {
    return (
        <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
            <SaveButton alwaysEnable />
            <DeleteButton mutationMode="pessimistic" redirect="/license/license_groups" />
        </Toolbar>
    );
};

interface LicenseGroupEditFormProps {
    setDescription: (value: string) => void;
}

const LicenseGroupEditForm = ({ setDescription }: LicenseGroupEditFormProps) => {
    const license_group = useRecordContext();
    const [descriptionSet, setDescriptionSet] = useState(false);

    if (!descriptionSet && license_group) {
        setDescription(license_group.description);
        setDescriptionSet(true);
    }

    return (
        <SimpleForm warnWhenUnsavedChanges toolbar={<CustomToolbar />}>
            <Typography variant="h6" sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}>
                <license_groups.icon />
                &nbsp;&nbsp;License Group
            </Typography>
            <TextInputWide autoFocus source="name" validate={validate_required_255} />
            <MarkdownEdit
                initialValue={license_group ? license_group.description : ""}
                setValue={setDescription}
                label="Description"
                maxLength={2048}
            />
            <BooleanInput source="is_public" label="Public" />
        </SimpleForm>
    );
};

const LicenseGroupEdit = () => {
    const [description, setDescription] = useState("");

    const transform = (data: any) => {
        data.description = description;
        return data;
    };

    return (
        <Edit redirect="show" mutationMode="pessimistic" transform={transform}>
            <LicenseGroupEditForm setDescription={setDescription} />
        </Edit>
    );
};

export default LicenseGroupEdit;
