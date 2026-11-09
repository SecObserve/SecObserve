import { useState } from "react";
import { Confirm, useDelete, useNotify, useRefresh } from "react-admin";

import RemoveButton from "../../commons/custom_fields/RemoveButton";
import { feature_scancodeio_integration } from "../../commons/functions";

type ServiceDeleteProps = {
    service: any;
};

const ServiceDelete = (props: ServiceDeleteProps) => {
    const [open, setOpen] = useState(false);
    const [deleted, setDeleted] = useState(false);
    const [error_shown, setErrorShown] = useState(false);
    const [deleteOne, { error }] = useDelete();
    const refresh = useRefresh();
    const notify = useNotify();
    const handleClick = () => setOpen(true);
    const handleDialogClose = () => setOpen(false);

    const handleConfirm = async () => {
        deleteOne("services", { id: props.service.id });
        setDeleted(true);
        refresh();
        setOpen(false);
    };

    if (error && !error_shown) {
        setErrorShown(true);
        setDeleted(false);
        notify("Service could not be deleted: " + error, {
            type: "warning",
        });
    } else if (deleted) {
        setDeleted(false);
        notify("Service deleted");
    }

    return (
        <>
            <RemoveButton title="Delete" onClick={handleClick} />
            <Confirm
                isOpen={open}
                title="Delete service"
                content={
                    "Are you sure you want to delete the service " +
                    props.service.name +
                    " and all of its observations?" +
                    (feature_scancodeio_integration()
                        ? " If it has a ScanCode.io project, that project is permanently deleted as well, including its inputs and results."
                        : "")
                }
                onConfirm={handleConfirm}
                onClose={handleDialogClose}
            />
        </>
    );
};

export default ServiceDelete;
