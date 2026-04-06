import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useRef, useState } from "react";
import { SimpleForm, useNotify, useRefresh } from "react-admin";

import MarkdownEdit from "../../commons/custom_fields/MarkdownEdit";
import RemoveButton from "../../commons/custom_fields/RemoveButton";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

const ObservationRemoveAssessment = () => {
    const dialogRef = useRef<HTMLDivElement>(null);
    const [comment, setComment] = useState("");
    const [open, setOpen] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();
    const handleOpen = () => setOpen(true);
    const handleCancel = () => setOpen(false);
    const handleClose = (event: object, reason: string) => {
        if (reason && reason == "backdropClick") return;
        setOpen(false);
    };

    const observationUpdate = async (data: any) => {
        if (comment === "") {
            notify("Comment is required", {
                type: "warning",
            });
            return;
        }

        const patch = {
            comment: comment,
        };

        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/observations/" + data.id + "/remove_assessment/", {
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

    return (
        <Fragment>
            <RemoveButton title="Remove Assessment" onClick={handleOpen} />
            <Dialog ref={dialogRef} open={open} onClose={handleClose} maxWidth={"lg"}>
                <DialogTitle>Observation Remove Assessment</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={observationUpdate}
                        toolbar={<ToolbarCancelSave onClick={handleCancel} alwaysEnable={true} />}
                    >
                        <MarkdownEdit
                            initialValue=""
                            setValue={setComment}
                            label="Comment *"
                            overlayContainer={dialogRef.current ?? null}
                            maxLength={4096}
                            autoFocus
                        />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default ObservationRemoveAssessment;
