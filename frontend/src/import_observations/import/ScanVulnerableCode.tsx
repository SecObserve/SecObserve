import UploadIcon from "@mui/icons-material/CloudUpload";
import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { SimpleForm, WithRecord, useNotify, useRefresh } from "react-admin";

import { BranchReferenceInput } from "../../commons/custom_fields/BranchReferenceInput";
import MenuButton from "../../commons/custom_fields/MenuButton";
import { Spinner } from "../../commons/custom_fields/Spinner";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { getIconAndFontColor } from "../../commons/functions";
import { TextInputWide } from "../../commons/layout/themes";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

interface ScanVulnerableCodeProps {
    product: any;
}

const ScanVulnerableCode = ({ product }: ScanVulnerableCodeProps) => {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();
    const handleOpen = () => setOpen(true);
    const handleCancel = () => {
        setOpen(false);
        setLoading(false);
    };
    const handleClose = (event: object, reason: string) => {
        if (reason && reason == "backdropClick") return;
        setOpen(false);
        setLoading(false);
    };

    const scanVulnerableCode = async (data: any) => {
        setLoading(true);

        let url;
        if (data.branch) {
            url =
                window.__RUNTIME_CONFIG__.API_BASE_URL +
                "/products/" +
                product.id +
                "/" +
                data.branch +
                "/scan_vulnerablecode/";
        } else {
            url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/products/" + product.id + "/scan_vulnerablecode/";
        }

        httpClient(url, {
            method: "POST",
        })
            .then((result) => {
                const message =
                    result.json.observations_new +
                    " new observations\n" +
                    result.json.observations_updated +
                    " updated observations\n" +
                    result.json.observations_resolved +
                    " resolved observations";
                refresh();
                setLoading(false);
                setOpen(false);
                notify(message, {
                    type: "success",
                    multiLine: true,
                });
            })
            .catch((error) => {
                setLoading(false);
                setOpen(false);
                notify(error.message, {
                    type: "warning",
                });
            });
    };

    return (
        <Fragment>
            <MenuButton
                title="Scan vulnerabilities from VulnerableCode"
                onClick={handleOpen}
                icon={<UploadIcon sx={{ color: getIconAndFontColor() }} />}
            />
            <Dialog open={open && !loading} onClose={handleClose}>
                <DialogTitle>Scan vulnerabilities from VulnerableCode</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={scanVulnerableCode}
                        toolbar={
                            <ToolbarCancelSave
                                onClick={handleCancel}
                                saveButtonLabel="Scan"
                                saveButtonIcon={<UploadIcon />}
                                alwaysEnable
                            />
                        }
                    >
                        <TextInputWide source="name" label="Product name" defaultValue={product.name} disabled />
                        <WithRecord
                            render={(product) => (
                                <Fragment>
                                    {product.has_branches && (
                                        <BranchReferenceInput
                                            source="branch"
                                            product={product.id}
                                            defaultValue={product.repository_default_branch}
                                            for_license_components={true}
                                        />
                                    )}
                                </Fragment>
                            )}
                        />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
            <Spinner open={loading && open} />
        </Fragment>
    );
};

export default ScanVulnerableCode;
