import { useState } from "react";
import { Confirm, useNotify, useRefresh } from "react-admin";

import RemoveButton from "../../commons/custom_fields/RemoveButton";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

type LicensePolicyItemRemoveProps = {
    license_policy_item: any;
};

const getItemName = (license_policy_item: any) => {
    if (license_policy_item.license_group_name) {
        return license_policy_item.license_group_name;
    }
    if (license_policy_item.license_spdx_id) {
        return license_policy_item.license_spdx_id;
    }
    if (license_policy_item.non_spdx_license) {
        return license_policy_item.non_spdx_license;
    }
    return "";
};

const LicensePolicyItemRemove = ({ license_policy_item }: LicensePolicyItemRemoveProps) => {
    const [open, setOpen] = useState(false);
    const [saving, setSaving] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();
    const handleClick = () => setOpen(true);
    const handleDialogClose = () => setOpen(false);

    const removeItem = async () => {
        const url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/license_policy_items/" + license_policy_item.id + "/";
        setSaving(true);
        httpClient(url, {
            method: "DELETE",
        })
            .then(() => {
                setOpen(false);
                refresh();
                notify("Item removed", { type: "success" });
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
                title="Remove license policy item"
                content={"Are you sure you want to remove the item " + getItemName(license_policy_item) + "?"}
                onConfirm={removeItem}
                onClose={handleDialogClose}
            />
        </>
    );
};

export default LicensePolicyItemRemove;
