import ChecklistIcon from "@mui/icons-material/Checklist";
import { useState } from "react";
import { Confirm, useListContext, useNotify, useRefresh, useUnselectAll } from "react-admin";

import SmallButton from "../commons/custom_fields/SmallButton";
import { Spinner } from "../commons/custom_fields/Spinner";
import { httpClient } from "../commons/ra-data-django-rest-framework";
import { update_notification_count } from "./notification_count";

const NotificationBulkMarkAsViewedButton = () => {
    const [open, setOpen] = useState(false);
    const { selectedIds } = useListContext();
    const refresh = useRefresh();
    const [loading, setLoading] = useState(false);
    const notify = useNotify();
    const unselectAll = useUnselectAll("notifications", "notifications.list");
    const handleClick = () => setOpen(true);
    const handleDialogClose = () => setOpen(false);

    const handleConfirm = async () => {
        setLoading(true);
        const url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/notifications/bulk_mark_as_viewed/";
        const delete_data = {
            notifications: selectedIds,
        };

        httpClient(url, {
            method: "POST",
            body: JSON.stringify(delete_data),
        })
            .then(() => {
                refresh();
                setOpen(false);
                setLoading(false);
                update_notification_count();
                unselectAll();
                notify("Notifications marked as viewed", {
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
            <SmallButton icon={<ChecklistIcon />} title="Mark as viewed" onClick={handleClick} />
            <Confirm
                isOpen={open && !loading}
                title="Mark as viewed"
                content="Are you sure you want to mark the selected notifications as viewed?"
                onConfirm={handleConfirm}
                onClose={handleDialogClose}
            />
            <Spinner open={open && loading} />
        </>
    );
};

export default NotificationBulkMarkAsViewedButton;
