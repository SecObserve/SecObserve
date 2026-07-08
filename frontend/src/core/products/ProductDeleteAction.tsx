import DeleteIcon from "@mui/icons-material/Delete";
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

    if (product.delete_request_pending && canRequestDelete) {
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
            notify(`Delete request created`, { type: "success" });
            closeDialog();
            refresh();
        } catch (error: any) {
            notify(`Delete request failed: ${error.message}`, { type: "error" });
        }
    };

    return (
        <>
            <Button
                variant="contained"
                color={hasDeletePermission ? "error" : "inherit"}
                startIcon={<DeleteIcon />}
                onClick={() => setOpen(true)}
            >
                {hasDeletePermission ? "Delete" : "Request deletion"}
            </Button>
            <Dialog open={open} onClose={closeDialog} fullWidth maxWidth="sm">
                <DialogTitle>{hasDeletePermission ? `Delete ${label}` : `Request ${label} deletion`}</DialogTitle>
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
                        <Typography sx={{ marginTop: 1 }}>
                            This will ask an Owner to approve deletion of <strong>{product.name}</strong>.
                        </Typography>
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
                            Request deletion
                        </Button>
                    )}
                </DialogActions>
            </Dialog>
        </>
    );
};

export default ProductDeleteAction;
