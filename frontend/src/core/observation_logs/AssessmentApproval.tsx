import ApprovalIcon from "@mui/icons-material/Approval";
import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useRef, useState } from "react";
import { ArrayInput, RaRecord, SimpleForm, SimpleFormIterator, useNotify, useRefresh } from "react-admin";

import MarkdownEdit from "../../commons/custom_fields/MarkdownEdit";
import SmallButton from "../../commons/custom_fields/SmallButton";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_required, validate_required_255 } from "../../commons/custom_validators";
import {
    justificationIsEnabledForStatus,
    remediationsAreEnabledForStatus,
    settings_vex_justification_style,
} from "../../commons/functions";
import { AutocompleteInputMedium, AutocompleteInputWide, TextInputWide } from "../../commons/layout/themes";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { VEX_JUSTIFICATION_TYPE_CSAF_OPENVEX, VEX_JUSTIFICATION_TYPE_CYCLONEDX } from "../../commons/types";
import {
    ASSESSMENT_STATUS_APPROVED,
    ASSESSMENT_STATUS_APPROVED_WITH_EDITS,
    ASSESSMENT_STATUS_CHOICES,
    ASSESSMENT_STATUS_REJECTED,
    OBSERVATION_CYCLONEDX_VEX_JUSTIFICATION_CHOICES,
    OBSERVATION_VEX_JUSTIFICATION_CHOICES,
    OBSERVATION_VEX_REMEDIATION_CATEGORY_CHOICES,
} from "../types";

type AssessmentApprovalProps = {
    observation_log: RaRecord;
};

const AssessmentApproval = ({ observation_log }: AssessmentApprovalProps) => {
    const dialogRef = useRef<HTMLDivElement>(null);
    const [open, setOpen] = useState(false);
    const [decision, setDecision] = useState(ASSESSMENT_STATUS_APPROVED);
    const [comment, setComment] = useState(observation_log.comment);
    const justificationEnabled = justificationIsEnabledForStatus(observation_log.status);
    const remediationsEnabled = remediationsAreEnabledForStatus(observation_log.status);
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
            if (justificationEnabled) {
                patch.observation_log_vex_justification = data.vex_justification;
            }
            if (remediationsEnabled) {
                patch.observation_log_vex_remediations = data.vex_remediations;
            }
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
                        {decision == ASSESSMENT_STATUS_APPROVED_WITH_EDITS &&
                            justificationEnabled &&
                            settings_vex_justification_style() === VEX_JUSTIFICATION_TYPE_CSAF_OPENVEX && (
                                <AutocompleteInputWide
                                    source="vex_justification"
                                    label="VEX justification"
                                    choices={OBSERVATION_VEX_JUSTIFICATION_CHOICES}
                                />
                            )}
                        {decision == ASSESSMENT_STATUS_APPROVED_WITH_EDITS &&
                            justificationEnabled &&
                            settings_vex_justification_style() === VEX_JUSTIFICATION_TYPE_CYCLONEDX && (
                                <AutocompleteInputWide
                                    source="vex_justification"
                                    label="VEX justification"
                                    choices={OBSERVATION_CYCLONEDX_VEX_JUSTIFICATION_CHOICES}
                                />
                            )}
                        {decision == ASSESSMENT_STATUS_APPROVED_WITH_EDITS && remediationsEnabled && (
                            <ArrayInput source="vex_remediations" defaultValue={""} label="VEX remediations">
                                <SimpleFormIterator disableReordering inline>
                                    <AutocompleteInputMedium
                                        source="category"
                                        label=""
                                        choices={OBSERVATION_VEX_REMEDIATION_CATEGORY_CHOICES}
                                    />
                                    <TextInputWide source="text" multiline={true} minRows={3} />
                                </SimpleFormIterator>
                            </ArrayInput>
                        )}
                    </SimpleForm>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default AssessmentApproval;
