import DeleteIcon from "@mui/icons-material/Delete";
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
import { useNotify } from "react-admin";

import MenuButton from "../commons/custom_fields/MenuButton";
import { getIconAndFontColor } from "../commons/functions";
import { httpClient } from "../commons/ra-data-django-rest-framework";

interface DeleteScanCodeIOProjectProps {
    scancodeio_project: any;
    onDeleted: () => void;
}

const DeleteScanCodeIOProject = ({ scancodeio_project, onDeleted }: DeleteScanCodeIOProjectProps) => {
    const [open, setOpen] = useState(false);
    const [confirmationName, setConfirmationName] = useState("");
    const [isDeleting, setIsDeleting] = useState(false);
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
            onDeleted();
        } catch (error: unknown) {
            const message = error instanceof Error ? error.message : String(error);
            notify(`Delete failed: ${message}`, { type: "error" });
            setIsDeleting(false);
        }
    };

    return (
        <Fragment>
            <MenuButton
                title="Delete ScanCode.io project"
                onClick={() => setOpen(true)}
                icon={<DeleteIcon sx={{ color: getIconAndFontColor() }} />}
                disabled={!scancodeio_project}
            />
            {scancodeio_project && (
                <Dialog open={open} onClose={closeDialog} fullWidth maxWidth="sm">
                    <DialogTitle>Delete ScanCode.io project</DialogTitle>
                    <DialogContent>
                        <Stack spacing={2} sx={{ marginTop: 1 }}>
                            <Typography>
                                This permanently deletes the project in ScanCode.io, including its inputs and results.
                                This action cannot be undone.
                            </Typography>
                            <Typography>
                                Type <strong>{scancodeio_project.project_name}</strong> to confirm permanent deletion.
                            </Typography>
                            <TextField
                                label="Confirmation name"
                                value={confirmationName}
                                onChange={(event) => setConfirmationName(event.target.value)}
                                onKeyDown={(event) => event.stopPropagation()}
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
            )}
        </Fragment>
    );
};

export default DeleteScanCodeIOProject;
