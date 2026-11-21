import PlaylistAddCheckIcon from "@mui/icons-material/PlaylistAddCheck";
import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useRef, useState } from "react";
import { ReferenceInput, SimpleForm, useNotify, useRefresh } from "react-admin";

import SmallButton from "../../commons/custom_fields/SmallButton";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_255 } from "../../commons/custom_validators";
import { AutocompleteInputExtraWide, TextInputExtraWide } from "../../commons/layout/themes";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

const ConcludedLicense = () => {
    const dialogRef = useRef<HTMLDivElement>(null);
    const [open, setOpen] = useState(false);
    const [saving, setSaving] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();

    const concludedLicenseUpdate = async (data: any) => {
        if (!data.manual_concluded_license_expression) {
            data.manual_concluded_license_expression = "";
        }
        if (!data.manual_concluded_non_spdx_license) {
            data.manual_concluded_non_spdx_license = "";
        }

        const patch = {
            manual_concluded_spdx_license: data.manual_concluded_spdx_license,
            manual_concluded_license_expression: data.manual_concluded_license_expression,
            manual_concluded_non_spdx_license: data.manual_concluded_non_spdx_license,
        };

        setSaving(true);
        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/license_components/" + data.id + "/concluded_license/", {
            method: "PATCH",
            body: JSON.stringify(patch),
        })
            .then(() => {
                refresh();
                notify("Concluded license updated", {
                    type: "success",
                });
                setOpen(false);
            })
            .catch((error) => {
                notify(error.message, {
                    type: "warning",
                });
            })
            .finally(() => setSaving(false));
    };

    const handleClose = (event: object, reason: string) => {
        if (reason && reason == "backdropClick") return;
        setOpen(false);
    };

    const handleCancel = () => setOpen(false);
    const handleOpen = () => setOpen(true);

    const validateFields = (values: any) => {
        const errors: any = {};

        // check if only one field is set
        const fields = [
            values.manual_concluded_spdx_license,
            values.manual_concluded_license_expression,
            values.manual_concluded_non_spdx_license,
        ];
        const filledFields = fields.filter(Boolean);
        if (filledFields.length > 1) {
            if (values.manual_concluded_spdx_license) {
                errors.manual_concluded_spdx_license = "Only one field must be set";
            }
            if (values.manual_concluded_license_expression) {
                errors.manual_concluded_license_expression = "Only one field must be set";
            }
            if (values.manual_concluded_non_spdx_license) {
                errors.manual_concluded_non_spdx_license = "Only one field must be set";
            }
        }

        return errors;
    };

    return (
        <Fragment>
            <SmallButton title="Add / edit concluded license" onClick={handleOpen} icon={<PlaylistAddCheckIcon />} />
            <Dialog ref={dialogRef} open={open} onClose={handleClose} maxWidth={"lg"}>
                <DialogTitle>Add / edit concluded license</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={concludedLicenseUpdate}
                        toolbar={<ToolbarCancelSave disabled={saving} onClick={handleCancel} />}
                        validate={validateFields}
                    >
                        <ReferenceInput
                            source="manual_concluded_spdx_license"
                            reference="licenses"
                            sort={{ field: "spdx_id", order: "ASC" }}
                        >
                            <AutocompleteInputExtraWide label="Concluded SPDX License" optionText="spdx_id_name" />
                        </ReferenceInput>
                        <TextInputExtraWide
                            source="manual_concluded_license_expression"
                            label="Concluded license expression"
                            validate={validate_255}
                        />
                        <TextInputExtraWide
                            source="manual_concluded_non_spdx_license"
                            label="Concluded Non-SPDX license"
                            validate={validate_255}
                        />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default ConcludedLicense;
