import { useState } from "react";
import { Confirm, useNotify, useRefresh } from "react-admin";

import RemoveButton from "../../commons/custom_fields/RemoveButton";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

type LicensePolicyAuthorizationGroupMemberRemoveProps = {
    license_policy_authorization_group_member: any;
};

const LicensePolicyAuthorizationGroupMemberRemove = ({
    license_policy_authorization_group_member,
}: LicensePolicyAuthorizationGroupMemberRemoveProps) => {
    const [open, setOpen] = useState(false);
    const [saving, setSaving] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();
    const handleClick = () => setOpen(true);
    const handleDialogClose = () => setOpen(false);

    const removeUser = async () => {
        const url =
            window.__RUNTIME_CONFIG__.API_BASE_URL +
            "/license_policy_authorization_group_members/" +
            license_policy_authorization_group_member.id +
            "/";
        setSaving(true);
        httpClient(url, {
            method: "DELETE",
        })
            .then(() => {
                setOpen(false);
                refresh();
                notify("Authorization group removed", { type: "success" });
            })
            .catch((error) => {
                notify(error.message, { type: "warning" });
            })
            .finally(() => setSaving(false));
    };

    return (
        <>
            <RemoveButton title="Remove" onClick={handleClick} />
            <Confirm
                loading={saving}
                isOpen={open}
                title="Remove authorization group"
                content={
                    "Are you sure you want to remove the authorization group " +
                    license_policy_authorization_group_member.authorization_group_data.name +
                    "?"
                }
                onConfirm={removeUser}
                onClose={handleDialogClose}
            />
        </>
    );
};

export default LicensePolicyAuthorizationGroupMemberRemove;
