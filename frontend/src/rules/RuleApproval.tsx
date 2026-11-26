import ApprovalIcon from "@mui/icons-material/Approval";
import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useRef, useState } from "react";
import { SimpleForm, useNotify, useRefresh } from "react-admin";

import MarkdownEdit from "../commons/custom_fields/MarkdownEdit";
import SmallButton from "../commons/custom_fields/SmallButton";
import { ToolbarCancelSave } from "../commons/custom_fields/ToolbarCancelSave";
import { validate_required } from "../commons/custom_validators";
import { AutocompleteInputMedium } from "../commons/layout/themes";
import { httpClient } from "../commons/ra-data-django-rest-framework";
import { RULE_STATUS_APPROVED, RULE_STATUS_CHOICES_APPROVAL, RULE_STATUS_REJECTED } from "./types";

type RuleApprovalProps = {
    rule_id: string | number;
    class: string;
};

const RuleApproval = (props: RuleApprovalProps) => {
    const dialogRef = useRef<HTMLDivElement>(null);
    const [open, setOpen] = useState(false);
    const [saving, setSaving] = useState(false);
    const [decision, setDecision] = useState(RULE_STATUS_APPROVED);
    const [rejectionRemark, setRejectionRemark] = useState("");
    const refresh = useRefresh();
    const notify = useNotify();

    const saveApproval = async (data: any) => {
        const patch: Record<string, string> = {
            approval_status: data.approval_status,
        };
        if (data.approval_status === RULE_STATUS_REJECTED) {
            if (!rejectionRemark.trim()) {
                notify("Remark for rejection is required", { type: "warning" });
                return;
            }
            patch.rejection_remark = rejectionRemark;
        }

        setSaving(true);
        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/" + props.class + "/" + props.rule_id + "/approval/", {
            method: "PATCH",
            body: JSON.stringify(patch),
        })
            .then(() => {
                setOpen(false);
                refresh();
                notify("Rule updated", {
                    type: "success",
                });
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
    const handleOpen = () => {
        setRejectionRemark("");
        setOpen(true);
    };

    return (
        <Fragment>
            <SmallButton title="Approval" onClick={handleOpen} icon={<ApprovalIcon />} />
            <Dialog ref={dialogRef} open={open} onClose={handleClose} maxWidth="lg">
                <DialogTitle sx={{ display: "flex", alignItems: "center" }}>
                    <ApprovalIcon />
                    &nbsp;&nbsp;Rule approval
                </DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={saveApproval}
                        toolbar={<ToolbarCancelSave disabled={saving} onClick={handleCancel} />}
                    >
                        <AutocompleteInputMedium
                            source="approval_status"
                            choices={RULE_STATUS_CHOICES_APPROVAL}
                            validate={validate_required}
                            label="Decision"
                            onChange={(e) => setDecision(e)}
                        />
                        {decision === RULE_STATUS_REJECTED && (
                            <MarkdownEdit
                                initialValue={rejectionRemark}
                                setValue={setRejectionRemark}
                                label="Remark for rejection *"
                                overlayContainer={dialogRef.current ?? null}
                                maxLength={4096}
                            />
                        )}
                    </SimpleForm>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default RuleApproval;
