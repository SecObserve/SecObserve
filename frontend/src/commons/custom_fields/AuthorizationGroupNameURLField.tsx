import { FieldProps, Identifier, useRecordContext } from "react-admin";

import TextUrlField from "./TextUrlField";

export const AuthorizationGroupNameURLField = (props: FieldProps) => {
    const record = useRecordContext(props);
    return record ? (
        <TextUrlField
            text={record.authorization_group_data.name}
            url={showAuthorizationGroup(record.authorization_group_data.id)}
        />
    ) : null;
};

const showAuthorizationGroup = (id: Identifier) => {
    return "#/authorization_groups/" + id + "/show";
};
