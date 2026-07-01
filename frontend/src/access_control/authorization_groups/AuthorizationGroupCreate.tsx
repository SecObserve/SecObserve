import { Typography } from "@mui/material";
import { Create, SimpleForm } from "react-admin";

import authorization_groups from ".";
import { validate_255, validate_required_255 } from "../../commons/custom_validators";
import { TextInputWide } from "../../commons/layout/themes";

const AuthorizationGroupCreate = () => {
    const transform = (data: any) => {
        data.oidc_group ??= "";
        return data;
    };

    return (
        <Create redirect="show" transform={transform}>
            <SimpleForm warnWhenUnsavedChanges>
                <Typography variant="h6" sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}>
                    <authorization_groups.icon />
                    &nbsp;&nbsp;Authorization Group
                </Typography>
                <TextInputWide autoFocus source="name" validate={validate_required_255} />
                <TextInputWide source="oidc_group" label="OIDC group" validate={validate_255} />
            </SimpleForm>
        </Create>
    );
};

export default AuthorizationGroupCreate;
