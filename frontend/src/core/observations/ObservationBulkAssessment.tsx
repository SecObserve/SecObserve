import PlaylistAddCheckIcon from "@mui/icons-material/PlaylistAddCheck";
import { Backdrop, CircularProgress, Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useRef, useState } from "react";
import {
    DateInput,
    FormDataConsumer,
    SimpleForm,
    useListContext,
    useNotify,
    useRefresh,
    useUnselectAll,
} from "react-admin";

import MarkdownEdit from "../../commons/custom_fields/MarkdownEdit";
import SmallButton from "../../commons/custom_fields/SmallButton";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_after_today } from "../../commons/custom_validators";
import {
    justificationIsEnabledForStatus,
    settings_risk_acceptance_expiry_date,
    settings_vex_justification_style,
} from "../../commons/functions";
import { AutocompleteInputMedium, AutocompleteInputWide } from "../../commons/layout/themes";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { VEX_JUSTIFICATION_TYPE_CSAF_OPENVEX, VEX_JUSTIFICATION_TYPE_CYCLONEDX } from "../../commons/types";
import {
    OBSERVATION_CYCLONEDX_VEX_JUSTIFICATION_CHOICES,
    OBSERVATION_SEVERITY_CHOICES,
    OBSERVATION_STATUS_CHOICES,
    OBSERVATION_STATUS_OPEN,
    OBSERVATION_STATUS_RISK_ACCEPTED,
    OBSERVATION_VEX_JUSTIFICATION_CHOICES,
} from "../types";

type ObservationBulkAssessmentButtonProps = {
    product: any;
    storeKey: string;
};

const ObservationBulkAssessment = ({ product, storeKey }: ObservationBulkAssessmentButtonProps) => {
    const dialogRef = useRef<HTMLDivElement>(null);
    const [comment, setComment] = useState("");
    const [open, setOpen] = useState(false);
    const [status, setStatus] = useState(OBSERVATION_STATUS_OPEN);
    const justificationEnabled = justificationIsEnabledForStatus(status);
    const refresh = useRefresh();
    const [loading, setLoading] = useState(false);
    const notify = useNotify();
    const { selectedIds } = useListContext();
    const unselectAll = useUnselectAll("observations", storeKey);

    const observationUpdate = async (data: any) => {
        if (comment === "") {
            notify("Comment is required", {
                type: "warning",
            });
            return;
        }
        setLoading(true);
        let url = "";
        if (product) {
            url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/products/" + product.id + "/observations_bulk_assessment/";
        } else {
            url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/observations/bulk_assessment/";
        }
        const assessment_data = {
            severity: data.current_severity,
            status: data.current_status,
            comment: comment,
            vex_justification: justificationEnabled ? data.current_vex_justification : "",
            observations: selectedIds,
            risk_acceptance_expiry_date: data.risk_acceptance_expiry_date,
        };

        httpClient(url, {
            method: "POST",
            body: JSON.stringify(assessment_data),
        })
            .then(() => {
                refresh();
                setOpen(false);
                setLoading(false);
                unselectAll();
                notify("Observations updated", {
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
            <SmallButton title="Assessment" onClick={handleOpen} icon={<PlaylistAddCheckIcon />} />
            <Dialog ref={dialogRef} open={open && !loading} onClose={handleClose} maxWidth={"lg"}>
                <DialogTitle>Bulk Observation Assessment</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={observationUpdate}
                        toolbar={<ToolbarCancelSave onClick={handleCancel} alwaysEnable={true} />}
                    >
                        <AutocompleteInputMedium
                            source="current_severity"
                            label="Severity"
                            choices={OBSERVATION_SEVERITY_CHOICES}
                        />
                        <AutocompleteInputMedium
                            source="current_status"
                            label="Status"
                            choices={OBSERVATION_STATUS_CHOICES}
                            onChange={(e) => setStatus(e)}
                        />
                        {justificationEnabled &&
                            settings_vex_justification_style() === VEX_JUSTIFICATION_TYPE_CSAF_OPENVEX && (
                                <AutocompleteInputWide
                                    source="current_vex_justification"
                                    label="VEX justification"
                                    choices={OBSERVATION_VEX_JUSTIFICATION_CHOICES}
                                />
                            )}
                        {justificationEnabled &&
                            settings_vex_justification_style() === VEX_JUSTIFICATION_TYPE_CYCLONEDX && (
                                <AutocompleteInputWide
                                    source="current_vex_justification"
                                    label="VEX justification"
                                    choices={OBSERVATION_CYCLONEDX_VEX_JUSTIFICATION_CHOICES}
                                />
                            )}
                        <FormDataConsumer>
                            {({ formData }) =>
                                formData.current_status &&
                                formData.current_status == OBSERVATION_STATUS_RISK_ACCEPTED &&
                                (formData.risk_acceptance_expiry_date_calculated ||
                                    settings_risk_acceptance_expiry_date()) && (
                                    <DateInput
                                        source="risk_acceptance_expiry_date"
                                        label="Risk acceptance expiry date"
                                        defaultValue={
                                            formData.risk_acceptance_expiry_date_calculated
                                                ? formData.risk_acceptance_expiry_date_calculated
                                                : settings_risk_acceptance_expiry_date()
                                        }
                                        validate={validate_after_today()}
                                    />
                                )
                            }
                        </FormDataConsumer>
                        <MarkdownEdit
                            initialValue=""
                            setValue={setComment}
                            label="Comment *"
                            overlayContainer={dialogRef.current ?? null}
                            maxLength={4096}
                        />
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

export default ObservationBulkAssessment;
