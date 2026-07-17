import ApprovalIcon from "@mui/icons-material/Approval";
import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useEffect, useRef, useState } from "react";
import { SimpleForm, useListContext, useNotify, useRefresh, useUnselectAll } from "react-admin";

import MarkdownEdit from "../../commons/custom_fields/MarkdownEdit";
import SmallButton from "../../commons/custom_fields/SmallButton";
import { Spinner } from "../../commons/custom_fields/Spinner";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_required, validate_required_255 } from "../../commons/custom_validators";
import { AutocompleteInputMedium, TextInputWide } from "../../commons/layout/themes";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import {
    ASSESSMENT_STATUS_APPROVED,
    ASSESSMENT_STATUS_APPROVED_WITH_EDITS,
    ASSESSMENT_STATUS_BULK_CHOICES,
    ASSESSMENT_STATUS_CHOICES,
    ASSESSMENT_STATUS_REJECTED,
} from "../types";

type AssessmentBulkApprovalProps = {
    storeKey: string;
};

const AssessmentBulkApproval = ({ storeKey }: AssessmentBulkApprovalProps) => {
    const dialogRef = useRef<HTMLDivElement>(null);
    const [open, setOpen] = useState(false);
    const [decision, setDecision] = useState(ASSESSMENT_STATUS_APPROVED);
    const refresh = useRefresh();
    const notify = useNotify();
    const { data = [], selectedIds } = useListContext();
    const unselectAll = useUnselectAll("observation_logs", storeKey);
    const [loading, setLoading] = useState(false);

    const selectedRecords = data.filter((record) => selectedIds.includes(record.id));

    const [comment, setComment] = useState("");

    const allSame =
        selectedRecords.length > 0 && selectedRecords.every((r) => r.comment === selectedRecords[0].comment);

    const firstComment = selectedRecords[0]?.comment ?? "";

    useEffect(() => {
        if (allSame) {
            setComment(firstComment);
        }
    }, [allSame, firstComment]);

    const assessmentUpdate = async (data: any) => {
        setLoading(true);
        let post_data: Record<string, any> = {
            assessment_status: data.assessment_status,
            rejection_remark: data.rejection_remark,
            observation_logs: selectedIds,
        };

        if (data.assessment_status === ASSESSMENT_STATUS_REJECTED) {
            post_data.rejection_remark = data.rejection_remark;
        }
        if (data.assessment_status === ASSESSMENT_STATUS_APPROVED_WITH_EDITS) {
            post_data.observation_log_comment = comment;
        }

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
            <Dialog open={open && !loading} onClose={handleClose} maxWidth="lg">
                <DialogTitle sx={{ display: "flex", alignItems: "center" }}>
                    <ApprovalIcon />
                    &nbsp;&nbsp;Assessment approval
                </DialogTitle>
                <DialogContent>
                    <SimpleForm onSubmit={assessmentUpdate} toolbar={<ToolbarCancelSave onClick={handleCancel} />}>
                        <AutocompleteInputMedium
                            source="assessment_status"
                            choices={allSame ? ASSESSMENT_STATUS_CHOICES : ASSESSMENT_STATUS_BULK_CHOICES}
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
                                initialValue={comment}
                                setValue={setComment}
                                label="Comment of Observation Log *"
                                overlayContainer={dialogRef.current ?? null}
                                maxLength={4096}
                            />
                        )}
                    </SimpleForm>
                </DialogContent>
            </Dialog>
            <Spinner open={loading && open} />
        </Fragment>
    );
};

export default AssessmentBulkApproval;
