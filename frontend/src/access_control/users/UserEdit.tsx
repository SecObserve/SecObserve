import { Divider, Typography } from "@mui/material";
import {
    BooleanInput,
    DeleteButton,
    Edit,
    FormDataConsumer,
    SaveButton,
    SelectInput,
    SimpleForm,
    Toolbar,
} from "react-admin";

import users from ".";
import { validate_150, validate_255, validate_required_150 } from "../../commons/custom_validators";
import { TextInputWide } from "../../commons/layout/themes";
import { INSTANCE_ROLE_CHOICES } from "../types";

const CustomToolbar = () => {
    return (
        <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
            <SaveButton />
            <DeleteButton mutationMode="pessimistic" redirect="/access_control/users" />
        </Toolbar>
    );
};

const UserEdit = () => {
    const transform = (data: any) => {
        data.full_name ??= "";
        data.first_name ??= "";
        data.last_name ??= "";
        data.email ??= "";
        // hidden inputs stay in the form state, so a regular user must not keep a chosen role
        if (!data.is_service_account) {
            data.instance_role = null;
        }
        return data;
    };

    return (
        <Edit redirect="show" mutationMode="pessimistic" transform={transform}>
            <SimpleForm warnWhenUnsavedChanges toolbar={<CustomToolbar />}>
                <Typography variant="h6" sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}>
                    <users.icon />
                    &nbsp;&nbsp;User
                </Typography>
                <TextInputWide autoFocus source="username" validate={validate_required_150} />
                <TextInputWide source="full_name" validate={validate_255} />
                <TextInputWide source="first_name" validate={validate_150} />
                <TextInputWide source="last_name" validate={validate_150} />
                <TextInputWide source="email" validate={validate_255} />
                <BooleanInput source="is_oidc_user" label="OIDC user" readOnly />
                <BooleanInput source="is_service_account" label="Service account" readOnly />

                <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />
                <Typography variant="h6" sx={{ marginBottom: 2 }}>
                    Permissions
                </Typography>
                <BooleanInput source="is_active" label="Active" />
                <BooleanInput source="is_external" label="External" />
                <BooleanInput source="is_superuser" label="Superuser" />
                <FormDataConsumer>
                    {({ formData }) =>
                        formData.is_service_account && (
                            <SelectInput
                                source="instance_role"
                                label="Instance role"
                                choices={INSTANCE_ROLE_CHOICES}
                                emptyText="No instance role"
                            />
                        )
                    }
                </FormDataConsumer>
            </SimpleForm>
        </Edit>
    );
};

export default UserEdit;
