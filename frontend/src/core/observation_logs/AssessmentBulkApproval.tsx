import ApprovalIcon from "@mui/icons-material/Approval";
import { Dialog, DialogContent, DialogTitle, Stack } from "@mui/material";
import { Fragment, ReactNode, useRef, useState } from "react";
import {
    BooleanInput,
    Confirm,
    FormDataConsumer,
    RaRecord,
    SimpleForm,
    useListContext,
    useNotify,
    useRefresh,
    useUnselectAll,
} from "react-admin";

import MarkdownEdit from "../../commons/custom_fields/MarkdownEdit";
import SmallButton from "../../commons/custom_fields/SmallButton";
import { Spinner } from "../../commons/custom_fields/Spinner";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_required, validate_required_255 } from "../../commons/custom_validators";
import { justificationIsEnabledForStatus, remediationsAreEnabledForStatus } from "../../commons/functions";
import { AutocompleteInputMedium, TextInputWide } from "../../commons/layout/themes";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import {
    ASSESSMENT_STATUS_APPROVED,
    ASSESSMENT_STATUS_APPROVED_WITH_EDITS,
    ASSESSMENT_STATUS_CHOICES,
    ASSESSMENT_STATUS_REJECTED,
} from "../types";
import { VEXJustificationInput, VEXRemediationsInput } from "./AssessmentApproval";

const remediationsKey = (record: RaRecord) =>
    JSON.stringify(
        record.vex_remediations?.length
            ? record.vex_remediations.map((remediation: any) => [remediation.category, remediation.text])
            : null
    );

const allEqual = (records: RaRecord[], key: (record: RaRecord) => string) =>
    records.every((record) => key(record) === key(records[0]));

type DifferentValuesProps = {
    source: string;
    label: string;
    count: number;
    children: ReactNode;
};

// A field whose values differ is kept per assessment, unless the approver changes it for all of them
const DifferentValues = ({ source, label, count, children }: DifferentValuesProps) => (
    <FormDataConsumer>
        {({ formData }) => (
            <Stack sx={{ width: "100%" }}>
                {formData["change_" + source] ? (
                    children
                ) : (
                    <TextInputWide
                        source={source + "_different"}
                        label={label}
                        disabled
                        helperText="The selected assessments have different values, each keeps its own"
                    />
                )}
                <BooleanInput source={"change_" + source} label={`Change for all ${count} assessments`} />
            </Stack>
        )}
    </FormDataConsumer>
);

type PendingChange = {
    data: Record<string, any>;
    changed: string[];
    kept: string[];
};

type AssessmentBulkApprovalProps = {
    storeKey: string;
};

const AssessmentBulkApproval = ({ storeKey }: AssessmentBulkApprovalProps) => {
    const dialogRef = useRef<HTMLDivElement>(null);
    const [open, setOpen] = useState(false);
    const [decision, setDecision] = useState(ASSESSMENT_STATUS_APPROVED);
    const [pending, setPending] = useState<PendingChange | null>(null);
    const refresh = useRefresh();
    const notify = useNotify();
    const { data = [], selectedIds } = useListContext();
    const unselectAll = useUnselectAll("observation_logs", storeKey);
    const [loading, setLoading] = useState(false);

    const selectedRecords = data.filter((record) => selectedIds.includes(record.id));
    const count = selectedRecords.length;
    const first = selectedRecords[0];

    const sameComment = allEqual(selectedRecords, (record) => record.comment ?? "");
    const sameJustification = allEqual(selectedRecords, (record) => record.vex_justification ?? "");
    const sameRemediations = allEqual(selectedRecords, remediationsKey);
    const [comment, setComment] = useState("");

    // Only offered when every selected assessment has a status the value applies to
    const justificationEnabled = count > 0 && selectedRecords.every((r) => justificationIsEnabledForStatus(r.status));
    const remediationsEnabled = count > 0 && selectedRecords.every((r) => remediationsAreEnabledForStatus(r.status));

    const send = (post_data: Record<string, any>) => {
        setPending(null);
        setLoading(true);
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

    const assessmentUpdate = async (data: any) => {
        const post_data: Record<string, any> = {
            assessment_status: data.assessment_status,
            observation_logs: selectedIds,
        };
        if (data.assessment_status === ASSESSMENT_STATUS_REJECTED) {
            post_data.rejection_remark = data.rejection_remark;
        }
        if (data.assessment_status !== ASSESSMENT_STATUS_APPROVED_WITH_EDITS) {
            send(post_data);
            return;
        }

        const fields = [
            {
                name: "VEX justification",
                source: "vex_justification",
                enabled: justificationEnabled,
                same: sameJustification,
            },
            {
                name: "VEX remediations",
                source: "vex_remediations",
                enabled: remediationsEnabled,
                same: sameRemediations,
            },
            { name: "comment", source: "comment", enabled: true, same: sameComment },
        ].filter((field) => field.enabled);
        const changed = fields.filter((field) => !field.same && data["change_" + field.source]);
        const kept = fields.filter((field) => !field.same && !data["change_" + field.source]);
        const sent = fields.filter((field) => field.same || data["change_" + field.source]);

        if (sent.length === 0) {
            notify("Change a field for all assessments, or choose Approved", { type: "warning" });
            return;
        }
        if (sent.some((field) => field.source === "comment") && !comment.trim()) {
            notify("The comment of the observation log is required", { type: "warning" });
            return;
        }
        for (const field of sent) {
            post_data["observation_log_" + field.source] = field.source === "comment" ? comment : data[field.source];
        }

        if (changed.length > 0) {
            setPending({
                data: post_data,
                changed: changed.map((field) => field.name),
                kept: kept.map((field) => field.name),
            });
        } else {
            send(post_data);
        }
    };

    const handleClose = (event: object, reason: string) => {
        if (reason && reason == "backdropClick") return;
        setOpen(false);
    };
    const handleCancel = () => setOpen(false);
    const handleOpen = () => {
        setDecision(ASSESSMENT_STATUS_APPROVED);
        setComment(sameComment ? (first?.comment ?? "") : "");
        setOpen(true);
    };

    const commentInput = (
        <MarkdownEdit
            initialValue={comment}
            setValue={setComment}
            label="Comment of Observation Log *"
            overlayContainer={dialogRef.current ?? null}
            maxLength={4096}
        />
    );

    return (
        <Fragment>
            <SmallButton title="Approval" onClick={handleOpen} icon={<ApprovalIcon />} />
            <Dialog ref={dialogRef} open={open && !loading} onClose={handleClose} maxWidth="lg">
                <DialogTitle sx={{ display: "flex", alignItems: "center" }}>
                    <ApprovalIcon />
                    &nbsp;&nbsp;Assessment approval
                </DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={assessmentUpdate}
                        toolbar={<ToolbarCancelSave onClick={handleCancel} />}
                        defaultValues={{
                            vex_justification: sameJustification ? first?.vex_justification : undefined,
                            vex_remediations:
                                sameRemediations && first?.vex_remediations?.length
                                    ? first.vex_remediations
                                    : undefined,
                        }}
                    >
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
                        {decision == ASSESSMENT_STATUS_APPROVED_WITH_EDITS &&
                            justificationEnabled &&
                            (sameJustification ? (
                                <VEXJustificationInput />
                            ) : (
                                <DifferentValues source="vex_justification" label="VEX justification" count={count}>
                                    <VEXJustificationInput validate={validate_required} />
                                </DifferentValues>
                            ))}
                        {decision == ASSESSMENT_STATUS_APPROVED_WITH_EDITS &&
                            remediationsEnabled &&
                            (sameRemediations ? (
                                <VEXRemediationsInput />
                            ) : (
                                <DifferentValues source="vex_remediations" label="VEX remediations" count={count}>
                                    <VEXRemediationsInput />
                                </DifferentValues>
                            ))}
                        {decision == ASSESSMENT_STATUS_APPROVED_WITH_EDITS &&
                            (sameComment ? (
                                commentInput
                            ) : (
                                <DifferentValues source="comment" label="Comment of Observation Log" count={count}>
                                    {commentInput}
                                </DifferentValues>
                            ))}
                    </SimpleForm>
                </DialogContent>
            </Dialog>
            <Confirm
                isOpen={pending !== null}
                title={`Change for all ${count} assessments?`}
                content={
                    <span>
                        The {pending?.changed.join(" and ")} of all {count} assessments will be replaced.
                        {pending &&
                            pending.kept.length > 0 &&
                            ` Each assessment keeps its own ${pending.kept.join(" and ")}.`}
                    </span>
                }
                onConfirm={() => pending && send(pending.data)}
                onClose={() => setPending(null)}
            />
            <Spinner open={loading && open} />
        </Fragment>
    );
};

export default AssessmentBulkApproval;
