import { FieldProps, Identifier, useRecordContext } from "react-admin";

import TextUrlField from "./TextUrlField";

export const UserFullNameURLField = (props: FieldProps) => {
    const record = useRecordContext(props);
    return record ? <TextUrlField text={record.user_data.full_name} url={showUser(record.user_data.id)} /> : null;
};

const showUser = (id: Identifier) => {
    return "#/users/" + id + "/show";
};
