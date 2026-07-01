import { Typography } from "@mui/material";
import { useState } from "react";
import { BooleanInput, Create, SimpleForm } from "react-admin";

import license_groups from ".";
import MarkdownEdit from "../../commons/custom_fields/MarkdownEdit";
import { validate_required_255 } from "../../commons/custom_validators";
import { TextInputWide } from "../../commons/layout/themes";

const LicenseGroupCreate = () => {
    const [description, setDescription] = useState("");

    const transform = (data: any) => {
        data.description = description;
        return data;
    };

    return (
        <Create redirect="show" transform={transform}>
            <SimpleForm warnWhenUnsavedChanges>
                <Typography variant="h6" sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}>
                    <license_groups.icon />
                    &nbsp;&nbsp;License Group
                </Typography>
                <TextInputWide autoFocus source="name" validate={validate_required_255} />
                <MarkdownEdit initialValue="" setValue={setDescription} label="Description" maxLength={2048} />
                <BooleanInput source="is_public" label="Public" />
            </SimpleForm>
        </Create>
    );
};

export default LicenseGroupCreate;
