import VisibilityIcon from "@mui/icons-material/Visibility";
import { useState } from "react";
import { Confirm, useNotify, useRefresh } from "react-admin";

import EditButton from "../../commons/custom_fields/EditButton";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

type DefaultBranchProps = {
    branch: any;
};

const DefaultBranch = ({ branch }: DefaultBranchProps) => {
    const notify = useNotify();
    const refresh = useRefresh();

    const [open, setOpen] = useState(false);
    const handleOpen = () => setOpen(true);
    const handleClose = () => setOpen(false);

    const setDefaultBranch = async () => {
        const patch = {
            is_default_branch: true,
        };
        const url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/branches/" + branch.id + "/";
        httpClient(url, {
            method: "PATCH",
            body: JSON.stringify(patch),
        })
            .then(() => {
                refresh();
                notify("Default branch / version set", {
                    type: "success",
                });
            })
            .catch((error) => {
                notify(error.message, {
                    type: "warning",
                });
            });

        setOpen(false);
    };

    return (
        <>
            <EditButton title="Default" onClick={handleOpen} icon={<VisibilityIcon />} />
            <Confirm
                isOpen={open}
                title="Set default branch / version"
                content={"Are you sure you want to set branch / version " + branch.name + " as default?"}
                onConfirm={setDefaultBranch}
                onClose={handleClose}
            />
        </>
    );
};

export default DefaultBranch;
