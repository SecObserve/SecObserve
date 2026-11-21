import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { SimpleForm, useNotify, useRefresh, useUpdate } from "react-admin";

import { ROLE_CHOICES } from "../../access_control/types";
import EditButton from "../../commons/custom_fields/EditButton";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_required } from "../../commons/custom_validators";
import { AutocompleteInputWide, TextInputWide } from "../../commons/layout/themes";

const ProductMemberEdit = () => {
    const [open, setOpen] = useState(false);
    const [update, { isPending }] = useUpdate();
    const refresh = useRefresh();
    const notify = useNotify();
    const handleOpen = () => setOpen(true);
    const handleCancel = () => setOpen(false);
    const handleClose = (event: object, reason: string) => {
        if (reason && reason == "backdropClick") return;
        setOpen(false);
    };

    const product_member_update = async (data: any) => {
        const patch = {
            role: data.role,
        };

        update(
            "product_members",

            {
                id: data.id,
                data: patch,
            },
            {
                onSuccess: () => {
                    setOpen(false);
                    refresh();
                    notify("User member updated", {
                        type: "success",
                    });
                },
                onError: (error: any) => {
                    notify(error.message, {
                        type: "warning",
                    });
                },
            }
        );
    };

    return (
        <Fragment>
            <EditButton title="Edit" onClick={handleOpen} />
            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>Edit user member</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={product_member_update}
                        toolbar={<ToolbarCancelSave disabled={isPending} onClick={handleCancel} />}
                    >
                        <TextInputWide source="user_data.full_name" label="User" disabled />
                        <AutocompleteInputWide source="role" choices={ROLE_CHOICES} validate={validate_required} />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default ProductMemberEdit;
