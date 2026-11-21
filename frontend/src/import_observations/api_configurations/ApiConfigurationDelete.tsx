import { useState } from "react";
import { Confirm, useDelete, useNotify, useRefresh } from "react-admin";

import RemoveButton from "../../commons/custom_fields/RemoveButton";

type APIConfigurationDeleteProps = {
    api_configuration: any;
};

const APIConfigurationDelete = (props: APIConfigurationDeleteProps) => {
    const [open, setOpen] = useState(false);
    const [deleteOne, { isPending }] = useDelete();
    const refresh = useRefresh();
    const notify = useNotify();
    const handleClick = () => setOpen(true);
    const handleDialogClose = () => setOpen(false);

    const handleConfirm = async () => {
        deleteOne(
            "api_configurations",
            { id: props.api_configuration.id },
            {
                onSuccess: () => {
                    setOpen(false);
                    refresh();
                    notify("API configuration deleted");
                },
                onError: (error: any) => {
                    notify("API configuration could not be deleted: " + error.message, {
                        type: "warning",
                    });
                },
            }
        );
    };

    return (
        <>
            <RemoveButton title="Delete" onClick={handleClick} />
            <Confirm
                loading={isPending}
                isOpen={open}
                title="Delete API configuration"
                content={"Are you sure you want to delete the API configuration " + props.api_configuration.name + "?"}
                onConfirm={handleConfirm}
                onClose={handleDialogClose}
            />
        </>
    );
};

export default APIConfigurationDelete;
