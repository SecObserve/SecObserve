import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import { Button } from "@mui/material";
import { useState } from "react";
import { Confirm, useNotify, useRefresh } from "react-admin";

import { Spinner } from "../../commons/custom_fields/Spinner";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

type PeriodicTaskRunNowProps = {
    task: string | null;
};

const PeriodicTaskRunNow = ({ task }: PeriodicTaskRunNowProps) => {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();
    const handleClick = () => setOpen(true);
    const handleDialogClose = () => setOpen(false);

    const handleConfirm = async () => {
        setLoading(true);

        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/periodic_tasks/run/", {
            method: "POST",
            body: JSON.stringify({ task: task }),
        })
            .then(() => {
                refresh();
                setOpen(false);
                setLoading(false);
                notify("Task enqueued", {
                    type: "success",
                });
            })
            .catch((error) => {
                refresh();
                setOpen(false);
                setLoading(false);
                notify(error.message, {
                    type: "warning",
                });
            });
    };

    return (
        <>
            <Button
                variant="contained"
                onClick={handleClick}
                disabled={task === null}
                startIcon={<PlayArrowIcon />}
                sx={{ width: "fit-content", fontSize: "0.8125rem", whiteSpace: "nowrap" }}
            >
                Run now
            </Button>
            <Confirm
                isOpen={open && !loading}
                title="Run now"
                content={
                    <span>
                        Are you sure you want to run the task <strong>{task}</strong> now?
                    </span>
                }
                onConfirm={handleConfirm}
                onClose={handleDialogClose}
            />
            <Spinner open={open && loading} />
        </>
    );
};

export default PeriodicTaskRunNow;
