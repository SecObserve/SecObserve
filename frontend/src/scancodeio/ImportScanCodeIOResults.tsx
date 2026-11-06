import SyncIcon from "@mui/icons-material/Sync";
import { Fragment, useState } from "react";
import { useNotify, useRefresh } from "react-admin";

import MenuButton from "../commons/custom_fields/MenuButton";
import { Spinner } from "../commons/custom_fields/Spinner";
import { getIconAndFontColor } from "../commons/functions";
import { httpClient } from "../commons/ra-data-django-rest-framework";

interface ImportScanCodeIOResultsProps {
    scancodeio_project: any;
    disabled: boolean;
}

const ImportScanCodeIOResults = ({ scancodeio_project, disabled }: ImportScanCodeIOResultsProps) => {
    const [loading, setLoading] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();

    const importResults = () => {
        setLoading(true);
        httpClient(
            window.__RUNTIME_CONFIG__.API_BASE_URL +
                "/scancodeio_projects/" +
                scancodeio_project.id +
                "/import_results/",
            { method: "POST" }
        )
            .then((result) => {
                const message =
                    result.json.license_components_new +
                    " new license components\n" +
                    result.json.license_components_updated +
                    " updated license components\n" +
                    result.json.license_components_deleted +
                    " deleted license components";
                refresh();
                setLoading(false);
                notify(message, {
                    type: "success",
                    multiLine: true,
                });
            })
            .catch((error) => {
                setLoading(false);
                notify(error.message, {
                    type: "warning",
                });
            });
    };

    return (
        <Fragment>
            <MenuButton
                title="Re-import results"
                onClick={importResults}
                icon={<SyncIcon sx={{ color: getIconAndFontColor() }} />}
                disabled={disabled}
            />
            <Spinner open={loading} />
        </Fragment>
    );
};

export default ImportScanCodeIOResults;
