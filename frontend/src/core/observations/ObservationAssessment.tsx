import PlaylistAddCheckIcon from "@mui/icons-material/PlaylistAddCheck";
import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useRef, useState } from "react";
import { DateInput, FormDataConsumer, NumberInput, SimpleForm, useNotify, useRefresh } from "react-admin";

import MarkdownEdit from "../../commons/custom_fields/MarkdownEdit";
import SmallButton from "../../commons/custom_fields/SmallButton";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_after_today } from "../../commons/custom_validators";
import { justificationIsEnabledForStatus, settings_vex_justification_style } from "../../commons/functions";
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

const ObservationAssessment = () => {
    const dialogRef = useRef<HTMLDivElement>(null);
    const [comment, setComment] = useState("");
    const [open, setOpen] = useState(false);
    const [status, setStatus] = useState(OBSERVATION_STATUS_OPEN);
    const justificationEnabled = justificationIsEnabledForStatus(status);
    const refresh = useRefresh();
    const notify = useNotify();

    const observationUpdate = async (data: any) => {
        if (comment === "") {
            notify("Comment is required", {
                type: "warning",
            });
            return;
        }

        const patch = {
            severity: data.severity,
            status: data.status,
            priority: data.priority,
            vex_justification: justificationEnabled ? data.vex_justification : "",
            comment: comment,
            risk_acceptance_expiry_date: data.risk_acceptance_expiry_date,
        };

        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/observations/" + data.id + "/assessment/", {
            method: "PATCH",
            body: JSON.stringify(patch),
        })
            .then(() => {
                refresh();
                notify("Observation updated", {
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
            <SmallButton title="Assessment" onClick={handleOpen} icon={<PlaylistAddCheckIcon />} />
            <Dialog ref={dialogRef} open={open} onClose={handleClose} maxWidth={"lg"}>
                <DialogTitle>Observation Assessment</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={observationUpdate}
                        toolbar={<ToolbarCancelSave onClick={handleCancel} alwaysEnable={true} />}
                    >
                        <AutocompleteInputMedium source="severity" choices={OBSERVATION_SEVERITY_CHOICES} />
                        <AutocompleteInputMedium
                            source="status"
                            choices={OBSERVATION_STATUS_CHOICES}
                            onChange={(e) => setStatus(e)}
                        />
                        <NumberInput source="priority" step={1} min={1} max={99} sx={{ width: "7em" }} />
                        {justificationEnabled &&
                            settings_vex_justification_style() === VEX_JUSTIFICATION_TYPE_CSAF_OPENVEX && (
                                <AutocompleteInputWide
                                    source="vex_justification"
                                    label="VEX justification"
                                    choices={OBSERVATION_VEX_JUSTIFICATION_CHOICES}
                                />
                            )}
                        {justificationEnabled &&
                            settings_vex_justification_style() === VEX_JUSTIFICATION_TYPE_CYCLONEDX && (
                                <AutocompleteInputWide
                                    source="vex_justification"
                                    label="VEX justification"
                                    choices={OBSERVATION_CYCLONEDX_VEX_JUSTIFICATION_CHOICES}
                                />
                            )}
                        <FormDataConsumer>
                            {({ formData }) =>
                                formData.status &&
                                formData.status == OBSERVATION_STATUS_RISK_ACCEPTED &&
                                formData.product_data.risk_acceptance_expiry_date_calculated && (
                                    <DateInput
                                        source="risk_acceptance_expiry_date"
                                        label="Risk acceptance expiry date"
                                        defaultValue={formData.product_data.risk_acceptance_expiry_date_calculated}
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
        </Fragment>
    );
};

export default ObservationAssessment;
