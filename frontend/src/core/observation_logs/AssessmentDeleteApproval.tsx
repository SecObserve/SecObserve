import DeleteIcon from "@mui/icons-material/Delete";
import { Backdrop, Button, CircularProgress } from "@mui/material";
import { Fragment, useState } from "react";
import { Confirm, useListContext, useNotify, useRefresh, useUnselectAll } from "react-admin";

import { httpClient } from "../../commons/ra-data-django-rest-framework";

type AssessmentDeleteApprovalProps = {
    storeKey: string;
};

const AssessmentDeleteApproval = ({ storeKey }: AssessmentDeleteApprovalProps) => {
    const [open, setOpen] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();
    const { selectedIds } = useListContext();
    const unselectAll = useUnselectAll("observation_logs", storeKey);
    const [loading, setLoading] = useState(false);

    const assessmentDelete = async () => {
        setLoading(true);
        const deleteBody = {
            observation_logs: selectedIds,
        };

        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/observation_logs/bulk_delete/", {
            method: "DELETE",
            body: JSON.stringify(deleteBody),
        })
            .then((response) => {
                refresh();
                setOpen(false);
                setLoading(false);
                unselectAll();
                const count = response.json.count;
                notify(`${count} assessment${count === 1 ? "" : "s"} deleted`, {
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

    const handleCancel = () => setOpen(false);
    const handleOpen = () => setOpen(true);

    return (
        <Fragment>
            <Button
                onClick={handleOpen}
                size="small"
                sx={{ paddingTop: "0px", paddingBottom: "2px" }}
                startIcon={<DeleteIcon />}
            >
                Delete
            </Button>
            <Confirm
                isOpen={open}
                title="Delete assessments"
                content={"Are you sure you want to delete the selected assessments?"}
                onConfirm={assessmentDelete}
                onClose={handleCancel}
            />
            {loading ? (
                <Backdrop sx={{ color: "#fff", zIndex: (theme) => theme.zIndex.drawer + 1 }} open={open}>
                    <CircularProgress color="primary" />
                </Backdrop>
            ) : null}
        </Fragment>
    );
};

export default AssessmentDeleteApproval;
