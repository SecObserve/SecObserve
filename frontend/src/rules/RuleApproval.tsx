import ApprovalIcon from "@mui/icons-material/Approval";
import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { SimpleForm, useNotify, useRefresh } from "react-admin";

import SmallButton from "../commons/custom_fields/SmallButton";
import { ToolbarCancelSave } from "../commons/custom_fields/ToolbarCancelSave";
import { validate_required, validate_required_255 } from "../commons/custom_validators";
import { AutocompleteInputMedium, TextInputWide } from "../commons/layout/themes";
import { httpClient } from "../commons/ra-data-django-rest-framework";
import { RULE_STATUS_CHOICES_APPROVAL } from "./types";

type RuleApprovalProps = {
    rule_id: string | number;
    class: string;
};

const RuleApproval = (props: RuleApprovalProps) => {
    const [open, setOpen] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();

    const saveApproval = async (data: any) => {
        const patch = {
            approval_status: data.approval_status,
            rejection_remark: data.rejection_remark,
        };

        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/" + props.class + "/" + props.rule_id + "/approval/", {
            method: "PATCH",
            body: JSON.stringify(patch),
        })
            .then(() => {
                refresh();
                notify("Rule updated", {
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

    const handleClose = (event: object, reason: string) => {
        if (reason && reason == "backdropClick") return;
        setOpen(false);
    };
    const handleCancel = () => setOpen(false);
    const handleOpen = () => setOpen(true);

    return (
        <Fragment>
            <SmallButton title="Approval" onClick={handleOpen} icon={<ApprovalIcon />} />
            <Dialog open={open} onClose={handleClose}>
                <DialogTitle sx={{ display: "flex", alignItems: "center" }}>
                    <ApprovalIcon />
                    &nbsp;&nbsp;Rule approval
                </DialogTitle>
                <DialogContent>
                    <SimpleForm onSubmit={saveApproval} toolbar={<ToolbarCancelSave onClick={handleCancel} />}>
                        <AutocompleteInputMedium
                            source="approval_status"
                            choices={RULE_STATUS_CHOICES_APPROVAL}
                            validate={validate_required}
                            label="Decision"
                        />
                        <TextInputWide source="rejection_remark" validate={validate_required_255} label="Remark" />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default RuleApproval;
