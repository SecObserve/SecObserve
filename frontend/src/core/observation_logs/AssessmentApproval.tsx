import ApprovalIcon from "@mui/icons-material/Approval";
import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useRef, useState } from "react";
import { RaRecord, SimpleForm, useNotify, useRefresh } from "react-admin";

import MarkdownEdit from "../../commons/custom_fields/MarkdownEdit";
import SmallButton from "../../commons/custom_fields/SmallButton";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_required, validate_required_255 } from "../../commons/custom_validators";
import { AutocompleteInputMedium, TextInputWide } from "../../commons/layout/themes";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import {
    ASSESSMENT_STATUS_APPROVED,
    ASSESSMENT_STATUS_APPROVED_WITH_EDITS,
    ASSESSMENT_STATUS_CHOICES,
    ASSESSMENT_STATUS_REJECTED,
} from "../types";

type AssessmentApprovalProps = {
    observation_log: RaRecord;
};

const AssessmentApproval = ({ observation_log }: AssessmentApprovalProps) => {
    const dialogRef = useRef<HTMLDivElement>(null);
    const [open, setOpen] = useState(false);
    const [decision, setDecision] = useState(ASSESSMENT_STATUS_APPROVED);
    const [comment, setComment] = useState("");
    const refresh = useRefresh();
    const notify = useNotify();

    const saveApproval = async (data: any) => {
        let patch: Record<string, any> = {
            assessment_status: data.assessment_status,
        };
        if (data.assessment_status === ASSESSMENT_STATUS_REJECTED) {
            patch.rejection_remark = data.rejection_remark;
        }
        if (data.assessment_status === ASSESSMENT_STATUS_APPROVED_WITH_EDITS) {
            patch.observation_log_comment = comment;
        }

        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/observation_logs/" + observation_log.id + "/approval/", {
            method: "PATCH",
            body: JSON.stringify(patch),
        })
            .then(() => {
                refresh();
                notify("Observation Log updated", {
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
            <Dialog ref={dialogRef} open={open} onClose={handleClose} maxWidth="lg">
                <DialogTitle sx={{ display: "flex", alignItems: "center" }}>
                    <ApprovalIcon />
                    &nbsp;&nbsp;Assessment approval
                </DialogTitle>
                <DialogContent dividers>
                    <SimpleForm onSubmit={saveApproval} toolbar={<ToolbarCancelSave onClick={handleCancel} />}>
                        <AutocompleteInputMedium
                            source="assessment_status"
                            choices={ASSESSMENT_STATUS_CHOICES}
                            validate={validate_required}
                            label="Decision"
                            onChange={(e) => setDecision(e)}
                        />
                        {decision == ASSESSMENT_STATUS_REJECTED && (
                            <TextInputWide
                                source="rejection_remark"
                                validate={validate_required_255}
                                label="Remark for rejection"
                            />
                        )}
                        {decision == ASSESSMENT_STATUS_APPROVED_WITH_EDITS && (
                            <MarkdownEdit
                                initialValue={observation_log.comment}
                                setValue={setComment}
                                label="Comment of Observation Log *"
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

export default AssessmentApproval;
