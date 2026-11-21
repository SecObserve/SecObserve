import { useState } from "react";
import { Confirm, useNotify, useRefresh } from "react-admin";

import RemoveButton from "../../commons/custom_fields/RemoveButton";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

type LicenseGroupLicenseRemoveProps = {
    license_group: any;
    license: any;
};

const LicenseGroupLicenseRemove = ({ license_group, license }: LicenseGroupLicenseRemoveProps) => {
    const [open, setOpen] = useState(false);
    const [saving, setSaving] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();
    const handleClick = () => setOpen(true);
    const handleDialogClose = () => setOpen(false);

    const removeLicense = async () => {
        const url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/license_groups/" + license_group.id + "/remove_license/";
        const body = JSON.stringify({ license: license.id });
        setSaving(true);
        httpClient(url, {
            method: "POST",
            body: body,
        })
            .then(() => {
                refresh();
                notify("License removed", { type: "success" });
                setOpen(false);
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
                title="Remove user"
                content={"Are you sure you want to remove the license " + license.spdx_id + "?"}
                onConfirm={removeLicense}
                onClose={handleDialogClose}
            />
        </>
    );
};

export default LicenseGroupLicenseRemove;
