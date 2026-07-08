import DeleteIcon from "@mui/icons-material/Delete";
import UndoIcon from "@mui/icons-material/Undo";
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useNotify, useRedirect, useRefresh } from "react-admin";

import {
    PERMISSION_PRODUCT_DELETE,
    PERMISSION_PRODUCT_EDIT,
    PERMISSION_PRODUCT_GROUP_DELETE,
    PERMISSION_PRODUCT_GROUP_EDIT,
} from "../../access_control/types";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { Product, ProductGroup } from "../types";

type ProductDeleteActionProps = {
    product: Product | ProductGroup | undefined;
    resource: "products" | "product_groups";
    isProductGroup: boolean;
};

const ProductDeleteAction = ({ product, resource, isProductGroup }: ProductDeleteActionProps) => {
    const [open, setOpen] = useState(false);
    const [confirmationName, setConfirmationName] = useState("");
    const notify = useNotify();
    const redirect = useRedirect();
    const refresh = useRefresh();

    if (!product) {
        return null;
    }

    const deletePermission = isProductGroup ? PERMISSION_PRODUCT_GROUP_DELETE : PERMISSION_PRODUCT_DELETE;
    const editPermission = isProductGroup ? PERMISSION_PRODUCT_GROUP_EDIT : PERMISSION_PRODUCT_EDIT;
    const hasDeletePermission = product.permissions?.includes(deletePermission);
    const canRequestDelete = product.permissions?.includes(editPermission) && !hasDeletePermission;
    const label = isProductGroup ? "product group" : "product";
    const currentUserId = getCurrentUserId();
    const isOwnDeleteRequest =
        product.delete_request_user != null && String(product.delete_request_user) === String(currentUserId);

    if (product.delete_request_pending && canRequestDelete && !isOwnDeleteRequest) {
        return (
            <Button variant="contained" color="inherit" startIcon={<DeleteIcon />} disabled>
                Delete requested
            </Button>
        );
    }

    if (!hasDeletePermission && !canRequestDelete) {
        return null;
    }

    const closeDialog = () => {
        setOpen(false);
        setConfirmationName("");
    };

    const forceDelete = async () => {
        try {
            await httpClient(`${window.__RUNTIME_CONFIG__.API_BASE_URL}/${resource}/${product.id}/force_delete/`, {
                method: "POST",
                body: JSON.stringify({ confirmation_name: confirmationName }),
            });
            notify(`${isProductGroup ? "Product group" : "Product"} deleted`, { type: "success" });
            redirect("list", resource);
        } catch (error: any) {
            notify(`Delete failed: ${error.message}`, { type: "error" });
        }
    };

    const requestDelete = async () => {
        try {
            await httpClient(`${window.__RUNTIME_CONFIG__.API_BASE_URL}/${resource}/${product.id}/request_delete/`, {
                method: "POST",
                body: JSON.stringify({}),
            });
            notify(`Delete request submitted`, { type: "success" });
            closeDialog();
            refresh();
        } catch (error: any) {
            notify(`Delete request failed: ${error.message}`, { type: "error" });
        }
    };

    const undoDeleteRequest = async () => {
        try {
            await httpClient(
                `${window.__RUNTIME_CONFIG__.API_BASE_URL}/${resource}/${product.id}/undo_delete_request/`,
                {
                    method: "POST",
                    body: JSON.stringify({}),
                }
            );
            notify(`Delete request undone`, { type: "success" });
            refresh();
        } catch (error: any) {
            notify(`Undo failed: ${error.message}`, { type: "error" });
        }
    };

    if (product.delete_request_pending && canRequestDelete && isOwnDeleteRequest) {
        return (
            <Button variant="contained" color="inherit" startIcon={<UndoIcon />} onClick={undoDeleteRequest}>
                Undo delete request
            </Button>
        );
    }

    return (
        <>
            <Button variant="contained" color="error" startIcon={<DeleteIcon />} onClick={() => setOpen(true)}>
                Delete
            </Button>
            <Dialog open={open} onClose={closeDialog} fullWidth maxWidth="sm">
                <DialogTitle>Delete {label}</DialogTitle>
                <DialogContent>
                    {hasDeletePermission ? (
                        <Stack spacing={2} sx={{ marginTop: 1 }}>
                            <Typography>
                                Type <strong>{product.name}</strong> to permanently delete this {label}.
                            </Typography>
                            <TextField
                                label="Confirmation name"
                                value={confirmationName}
                                onChange={(event) => setConfirmationName(event.target.value)}
                                autoFocus
                                fullWidth
                            />
                        </Stack>
                    ) : (
                        <Stack spacing={2} sx={{ marginTop: 1 }}>
                            <Typography>
                                Deletion of <strong>{product.name}</strong> requires Owner approval.
                            </Typography>
                            <Typography>
                                Submit a delete request so an Owner can review and approve permanent deletion of this
                                {` ${label}`}.
                            </Typography>
                        </Stack>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={closeDialog} color="inherit">
                        Cancel
                    </Button>
                    {hasDeletePermission ? (
                        <Button
                            onClick={forceDelete}
                            color="error"
                            variant="contained"
                            disabled={confirmationName !== product.name}
                        >
                            Delete
                        </Button>
                    ) : (
                        <Button onClick={requestDelete} variant="contained">
                            Request approval
                        </Button>
                    )}
                </DialogActions>
            </Dialog>
        </>
    );
};

function getCurrentUserId() {
    const currentUser = localStorage.getItem("user");
    if (!currentUser) {
        return null;
    }

    try {
        return JSON.parse(currentUser).id;
    } catch {
        return null;
    }
}

export default ProductDeleteAction;
