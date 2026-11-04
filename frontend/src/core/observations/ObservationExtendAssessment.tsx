import EventRepeatIcon from "@mui/icons-material/EventRepeat";
import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useRef, useState } from "react";
import {
    DateInput,
    Identifier,
    SimpleForm,
    useListContext,
    useNotify,
    useRecordContext,
    useRefresh,
    useUnselectAll,
} from "react-admin";

import MarkdownEdit from "../../commons/custom_fields/MarkdownEdit";
import SmallButton from "../../commons/custom_fields/SmallButton";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_after_today } from "../../commons/custom_validators";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { OBSERVATION_STATUS_RISK_ACCEPTED } from "../types";

type ExtendAssessmentProps = {
    title: string;
    url: string;
    method: string;
    observations?: Identifier[];
    defaultDate?: string;
    onDone?: () => void;
};

const ExtendAssessment = ({ title, url, method, observations, defaultDate, onDone }: ExtendAssessmentProps) => {
    const dialogRef = useRef<HTMLDivElement>(null);
    const [comment, setComment] = useState("");
    const [open, setOpen] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();

    const extend = async (data: any) => {
        if (comment === "") {
            notify("Comment is required", {
                type: "warning",
            });
            return;
        }

        // Without a date, the backend calculates it from the product settings
        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + url, {
            method: method,
            body: JSON.stringify({
                comment: comment,
                observations: observations,
                risk_acceptance_expiry_date: data.risk_acceptance_expiry_date || undefined,
            }),
        })
            .then(() => {
                refresh();
                onDone?.();
                notify("Assessment extended", {
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

    return (
        <Fragment>
            <SmallButton title="Extend" onClick={() => setOpen(true)} icon={<EventRepeatIcon />} />
            <Dialog ref={dialogRef} open={open} onClose={handleClose} maxWidth={"lg"}>
                <DialogTitle>{title}</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        record={{ risk_acceptance_expiry_date: defaultDate }}
                        onSubmit={extend}
                        toolbar={<ToolbarCancelSave onClick={() => setOpen(false)} alwaysEnable={true} />}
                    >
                        <DateInput
                            source="risk_acceptance_expiry_date"
                            label="New expiry date"
                            helperText="Calculated from the product settings if empty"
                            validate={validate_after_today()}
                        />
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

const ObservationExtendAssessment = () => {
    const observation = useRecordContext();
    return (
        <ExtendAssessment
            title="Extend Assessment"
            url={"/observations/" + observation?.id + "/extend_assessment/"}
            method="PATCH"
            defaultDate={
                observation?.current_status == OBSERVATION_STATUS_RISK_ACCEPTED
                    ? observation?.product_data?.risk_acceptance_expiry_date_calculated
                    : undefined
            }
        />
    );
};

export const ObservationBulkExtendAssessment = ({ storeKey }: { storeKey: string }) => {
    const { selectedIds } = useListContext();
    const unselectAll = useUnselectAll("observations", storeKey);
    return (
        <ExtendAssessment
            title="Bulk Extend Assessment"
            url="/observations/bulk_extend_assessment/"
            method="POST"
            observations={selectedIds}
            onDone={unselectAll}
        />
    );
};

export default ObservationExtendAssessment;
