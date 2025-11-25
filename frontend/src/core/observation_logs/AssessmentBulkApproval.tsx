import ApprovalIcon from "@mui/icons-material/Approval";
import { Backdrop, CircularProgress, Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { SimpleForm, useListContext, useNotify, useRefresh, useUnselectAll } from "react-admin";

import SmallButton from "../../commons/custom_fields/SmallButton";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_required, validate_required_255 } from "../../commons/custom_validators";
import { AutocompleteInputMedium, TextInputWide } from "../../commons/layout/themes";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { ASSESSMENT_STATUS_CHOICES } from "../types";

type AssessmentBulkApprovalProps = {
    storeKey: string;
};

const AssessmentBulkApproval = ({ storeKey }: AssessmentBulkApprovalProps) => {
    const [open, setOpen] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();
    const { selectedIds } = useListContext();
    const unselectAll = useUnselectAll("observation_logs", storeKey);
    const [loading, setLoading] = useState(false);

    const assessmentUpdate = async (data: any) => {
        setLoading(true);
        const post_data = {
            assessment_status: data.assessment_status,
            approval_remark: data.approval_remark,
            observation_logs: selectedIds,
        };

        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/observation_logs/bulk_approval/", {
            method: "POST",
            body: JSON.stringify(post_data),
        })
            .then(() => {
                refresh();
                setOpen(false);
                setLoading(false);
                unselectAll();
                notify("Assessments updated", {
                    type: "success",
                });
            })
            .catch((error) => {
                refresh();
                setOpen(false);
                setLoading(false);
                unselectAll();
                notify(error.message, {
                    type: "warning",
                });
            });
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
            <Dialog open={open && !loading} onClose={handleClose}>
                <DialogTitle sx={{ display: "flex", alignItems: "center" }}>
                    <ApprovalIcon />
                    &nbsp;&nbsp;Assessment approval
                </DialogTitle>
                <DialogContent>
                    <SimpleForm onSubmit={assessmentUpdate} toolbar={<ToolbarCancelSave onClick={handleCancel} />}>
                        <AutocompleteInputMedium
                            source="assessment_status"
                            choices={ASSESSMENT_STATUS_CHOICES}
                            validate={validate_required}
                            label="Decision"
                        />
                        <TextInputWide source="approval_remark" validate={validate_required_255} label="Remark" />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
            {loading ? (
                <Backdrop sx={{ color: "#fff", zIndex: (theme) => theme.zIndex.drawer + 1 }} open={open}>
                    <CircularProgress color="primary" />
                </Backdrop>
            ) : null}
        </Fragment>
    );
};

export default AssessmentBulkApproval;
