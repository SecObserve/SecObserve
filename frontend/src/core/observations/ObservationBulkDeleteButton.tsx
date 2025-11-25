import { Backdrop, CircularProgress } from "@mui/material";
import { useState } from "react";
import { Confirm, useListContext, useNotify, useRefresh, useUnselectAll } from "react-admin";

import RemoveButton from "../../commons/custom_fields/RemoveButton";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

type ObservationBulkDeleteButtonProps = {
    product: any;
    storeKey: string;
};

const ObservationBulkDeleteButton = ({ product, storeKey }: ObservationBulkDeleteButtonProps) => {
    const [open, setOpen] = useState(false);
    const { selectedIds } = useListContext();
    const refresh = useRefresh();
    const [loading, setLoading] = useState(false);
    const notify = useNotify();
    const unselectAll = useUnselectAll("observations", storeKey);
    const handleClick = () => setOpen(true);
    const handleDialogClose = () => setOpen(false);

    const handleConfirm = async () => {
        setLoading(true);
        const url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/products/" + product.id + "/observations_bulk_delete/";
        const delete_data = {
            observations: selectedIds,
        };

        httpClient(url, {
            method: "POST",
            body: JSON.stringify(delete_data),
        })
            .then(() => {
                refresh();
                setOpen(false);
                setLoading(false);
                unselectAll();
                notify("Observations deleted", {
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

    return (
        <>
            <RemoveButton title="Delete" onClick={handleClick} />
            <Confirm
                isOpen={open && !loading}
                title="Delete Observations"
                content="Are you sure you want to delete the selected observations?"
                onConfirm={handleConfirm}
                onClose={handleDialogClose}
            />
            {loading ? (
                <Backdrop sx={{ color: "#fff", zIndex: (theme) => theme.zIndex.drawer + 1 }} open={open}>
                    <CircularProgress color="primary" />
                </Backdrop>
            ) : null}
        </>
    );
};

export default ObservationBulkDeleteButton;
