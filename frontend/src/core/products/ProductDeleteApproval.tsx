import ApprovalIcon from "@mui/icons-material/Approval";
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useNotify, useRedirect, useRefresh } from "react-admin";

import { PERMISSION_PRODUCT_DELETE, PERMISSION_PRODUCT_GROUP_DELETE } from "../../access_control/types";
import { humanReadableDate } from "../../commons/functions";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { Product, ProductGroup } from "../types";

type ProductDeleteApprovalProps = {
    product: Product | ProductGroup | undefined;
    resource: "products" | "product_groups";
    isProductGroup: boolean;
};

const ProductDeleteApproval = ({ product, resource, isProductGroup }: ProductDeleteApprovalProps) => {
    const [open, setOpen] = useState(false);
    const [confirmationName, setConfirmationName] = useState("");
    const notify = useNotify();
    const redirect = useRedirect();
    const refresh = useRefresh();

    if (!product?.delete_request_pending) {
        return null;
    }

    const deletePermission = isProductGroup ? PERMISSION_PRODUCT_GROUP_DELETE : PERMISSION_PRODUCT_DELETE;
    if (!product.permissions?.includes(deletePermission)) {
        return null;
    }

    const label = isProductGroup ? "product group" : "product";

    const closeDialog = () => {
        setOpen(false);
        setConfirmationName("");
    };

    const approveDelete = async () => {
        try {
            await httpClient(
                `${window.__RUNTIME_CONFIG__.API_BASE_URL}/${resource}/${product.id}/approve_delete_request/`,
                {
                    method: "POST",
                    body: JSON.stringify({ confirmation_name: confirmationName }),
                }
            );
            notify(`Delete request approved`, { type: "success" });
            redirect("list", resource);
        } catch (error: any) {
            notify(`Approval failed: ${error.message}`, { type: "error" });
        }
    };

    const rejectDelete = async () => {
        try {
            await httpClient(
                `${window.__RUNTIME_CONFIG__.API_BASE_URL}/${resource}/${product.id}/reject_delete_request/`,
                {
                    method: "POST",
                    body: JSON.stringify({}),
                }
            );
            notify(`Delete request rejected`, { type: "success" });
            closeDialog();
            refresh();
        } catch (error: any) {
            notify(`Rejection failed: ${error.message}`, { type: "error" });
        }
    };

    return (
        <>
            <Button variant="contained" color="warning" startIcon={<ApprovalIcon />} onClick={() => setOpen(true)}>
                Review deletion
            </Button>
            <Dialog open={open} onClose={closeDialog} fullWidth maxWidth="sm">
                <DialogTitle>Review {label} deletion</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ marginTop: 1 }}>
                        <Typography>
                            <strong>{product.delete_request_user_full_name || "A maintainer"}</strong> requested
                            deletion
                            {product.delete_request_requested_at
                                ? ` on ${humanReadableDate(product.delete_request_requested_at)}`
                                : ""}
                            .
                        </Typography>
                        <Typography>
                            Type <strong>{product.name}</strong> to approve and permanently delete this {label}.
                        </Typography>
                        <TextField
                            label="Confirmation name"
                            value={confirmationName}
                            onChange={(event) => setConfirmationName(event.target.value)}
                            autoFocus
                            fullWidth
                        />
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={closeDialog} color="inherit">
                        Cancel
                    </Button>
                    <Button onClick={rejectDelete} color="inherit">
                        Reject
                    </Button>
                    <Button
                        onClick={approveDelete}
                        color="error"
                        variant="contained"
                        disabled={confirmationName !== product.name}
                    >
                        Approve deletion
                    </Button>
                </DialogActions>
            </Dialog>
        </>
    );
};

export default ProductDeleteApproval;
