import { useState } from "react";
import { Confirm, useDelete, useNotify, useRefresh } from "react-admin";

import RemoveButton from "../../commons/custom_fields/RemoveButton";
import { Spinner } from "../../commons/custom_fields/Spinner";
import { feature_scancodeio_integration } from "../../commons/functions";

type BranchDeleteProps = {
    branch: any;
};

const BranchDelete = (props: BranchDeleteProps) => {
    const [open, setOpen] = useState(false);
    const [deleteOne, { isPending }] = useDelete();
    const refresh = useRefresh();
    const notify = useNotify();
    const handleClick = () => setOpen(true);
    const handleDialogClose = () => setOpen(false);

    const handleConfirm = async () => {
        deleteOne(
            "branches",
            { id: props.branch.id },
            {
                onSuccess: () => {
                    setOpen(false);
                    refresh();
                    notify("Branch / version deleted");
                },
                onError: (error: any) => {
                    notify("Branch / version could not be deleted: " + error.message, {
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
                isOpen={open && !isPending}
                title="Delete branch / version"
                content={
                    "Are you sure you want to delete the branch / version " +
                    props.branch.name +
                    " and all of its observations?" +
                    (feature_scancodeio_integration()
                        ? " If it has a ScanCode.io project, that project is permanently deleted as well, including its inputs and results."
                        : "")
                }
                onConfirm={handleConfirm}
                onClose={handleDialogClose}
            />
            <Spinner open={open && isPending} />
        </>
    );
};

export default BranchDelete;
