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
import { useState } from "react";
import { Button as RaButton, useNotify, useRedirect } from "react-admin";

import { PERMISSION_PRODUCT_DELETE, PERMISSION_PRODUCT_GROUP_DELETE } from "../../access_control/types";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { Product, ProductGroup } from "../types";

type ProductDeleteActionProps = {
    product: Product | ProductGroup | undefined;
    isProductGroup: boolean;
};

const ProductDeleteAction = ({ product, isProductGroup }: ProductDeleteActionProps) => {
    const [open, setOpen] = useState(false);
    const [confirmationName, setConfirmationName] = useState("");
    const [isDeleting, setIsDeleting] = useState(false);
    const notify = useNotify();
    const redirect = useRedirect();

    if (!product) {
        return null;
    }

    const deletePermission = isProductGroup ? PERMISSION_PRODUCT_GROUP_DELETE : PERMISSION_PRODUCT_DELETE;
    if (!product.permissions?.includes(deletePermission)) {
        return null;
    }

    const label = isProductGroup ? "product group" : "product";
    const resource = isProductGroup ? "product_groups" : "products";
    const warning = isProductGroup
        ? "This permanently deletes the product group, all child products, and their observations, license findings, branches, services, and other related data."
        : "This permanently deletes the product and its observations, license findings, branches, services, and other related data.";

    const closeDialog = () => {
        if (isDeleting) {
            return;
        }
        setOpen(false);
        setConfirmationName("");
    };

    const deleteProduct = async () => {
        setIsDeleting(true);
        try {
            const query = new URLSearchParams({ name: confirmationName });
            const response = await httpClient(
                `${window.__RUNTIME_CONFIG__.API_BASE_URL}/${resource}/${product.id}/?${query.toString()}`,
                { method: "DELETE" }
            );
            if (response.status !== 204) {
                throw new Error(`Unexpected response status ${response.status}`);
            }
            notify(`${isProductGroup ? "Product group" : "Product"} deleted`, { type: "success" });
            redirect("list", resource);
        } catch (error: unknown) {
            const message = error instanceof Error ? error.message : String(error);
            notify(`Delete failed: ${message}`, { type: "error" });
            setIsDeleting(false);
        }
    };

    return (
        <>
            <RaButton label="ra.action.delete" color="error" onClick={() => setOpen(true)}>
                <DeleteIcon />
            </RaButton>
            <Dialog open={open} onClose={closeDialog} fullWidth maxWidth="sm">
                <DialogTitle>Delete {label}</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ marginTop: 1 }}>
                        <Typography>{warning} This action cannot be undone.</Typography>
                        <Typography>
                            Type <strong>{product.name}</strong> to confirm permanent deletion.
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
                        onClick={deleteProduct}
                        color="error"
                        variant="contained"
                        disabled={isDeleting || confirmationName !== product.name}
                    >
                        {isDeleting ? "Deleting..." : "Delete permanently"}
                    </MuiButton>
                </DialogActions>
            </Dialog>
        </>
    );
};

export default ProductDeleteAction;
