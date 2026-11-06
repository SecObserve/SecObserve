import {
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Button as MuiButton,
    Stack,
    TextField,
    Typography,
} from "@mui/material";
import { Fragment, useState } from "react";
import { useNotify, useRefresh } from "react-admin";

import RemoveButton from "../commons/custom_fields/RemoveButton";
import { httpClient } from "../commons/ra-data-django-rest-framework";

interface DeleteScanCodeIOProjectProps {
    scancodeio_project: any;
}

const DeleteScanCodeIOProject = ({ scancodeio_project }: DeleteScanCodeIOProjectProps) => {
    const [open, setOpen] = useState(false);
    const [confirmationName, setConfirmationName] = useState("");
    const [isDeleting, setIsDeleting] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();

    const closeDialog = () => {
        if (isDeleting) {
            return;
        }
        setOpen(false);
        setConfirmationName("");
    };

    const deleteProject = async () => {
        setIsDeleting(true);
        try {
            const query = new URLSearchParams({ name: confirmationName });
            await httpClient(
                `${window.__RUNTIME_CONFIG__.API_BASE_URL}/scancodeio_projects/${scancodeio_project.id}/?${query.toString()}`,
                { method: "DELETE" }
            );
            notify("ScanCode.io project deleted", { type: "success" });
            setIsDeleting(false);
            setOpen(false);
            setConfirmationName("");
            refresh();
        } catch (error: unknown) {
            const message = error instanceof Error ? error.message : String(error);
            notify(`Delete failed: ${message}`, { type: "error" });
            setIsDeleting(false);
        }
    };

    return (
        <Fragment>
            <RemoveButton title="Delete" onClick={() => setOpen(true)} />
            <Dialog open={open} onClose={closeDialog} fullWidth maxWidth="sm">
                <DialogTitle>Delete ScanCode.io project</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ marginTop: 1 }}>
                        <Typography>
                            This permanently deletes the project in ScanCode.io, including its inputs and results. This
                            action cannot be undone.
                        </Typography>
                        <Typography>
                            Type <strong>{scancodeio_project.project_name}</strong> to confirm permanent deletion.
                        </Typography>
                        <TextField
                            label="Confirmation name"
                            value={confirmationName}
                            onChange={(event) => setConfirmationName(event.target.value)}
                            disabled={isDeleting}
                            autoFocus
                            fullWidth
                        />
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <MuiButton onClick={closeDialog} color="inherit" disabled={isDeleting}>
                        Cancel
                    </MuiButton>
                    <MuiButton
                        onClick={deleteProject}
                        color="error"
                        variant="contained"
                        disabled={isDeleting || confirmationName !== scancodeio_project.project_name}
                    >
                        {isDeleting ? "Deleting..." : "Delete permanently"}
                    </MuiButton>
                </DialogActions>
            </Dialog>
        </Fragment>
    );
};

export default DeleteScanCodeIOProject;
