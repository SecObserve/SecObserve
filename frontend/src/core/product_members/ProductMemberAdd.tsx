import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { ReferenceInput, SaveButton, SimpleForm, useCreate, useNotify, useRefresh } from "react-admin";
import { useFormContext } from "react-hook-form";

import { ROLE_CHOICES } from "../../access_control/types";
import AddButton from "../../commons/custom_fields/AddButton";
import CancelButton from "../../commons/custom_fields/CancelButton";
import Toolbar from "../../commons/custom_fields/Toolbar";
import { validate_required } from "../../commons/custom_validators";
import { getUserOptionText } from "../../commons/functions";
import { AutocompleteInputWide } from "../../commons/layout/themes";

export type ProductMemberAddProps = {
    id: any;
};

const ProductMemberAdd = ({ id }: ProductMemberAddProps) => {
    const [open, setOpen] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();
    const [create] = useCreate();
    const handleOpen = () => setOpen(true);
    const handleCancel = () => {
        resetState();
        setOpen(false);
    };
    const handleClose = (event: object, reason: string) => {
        if (reason && reason == "backdropClick") return;
        resetState();
        setOpen(false);
    };

    const [user, setUser] = useState();
    const [role, setRole] = useState();
    const resetState = () => {
        setUser(undefined);
        setRole(undefined);
    };

    const CustomToolbar = () => {
        const { reset } = useFormContext();

        const handleSaveContinue = (e: any) => {
            e.preventDefault(); // necessary to prevent default SaveButton submit logic
            const data = {
                user: user,
                role: role,
            };
            add_product_member(data, false);
        };

        const handleSaveClose = (e: any) => {
            e.preventDefault(); // necessary to prevent default SaveButton submit logic
            const data = {
                user: user,
                role: role,
            };
            add_product_member(data, true);
        };

        const add_product_member = (data: any, close_dialog: boolean) => {
            data.product = id;
            create(
                "product_members",
                { data: data },
                {
                    onSuccess: () => {
                        refresh();
                        notify("User member added", { type: "success" });
                        resetState();
                        reset();
                        if (close_dialog) {
                            setOpen(false);
                        }
                    },
                    onError: (error: any) => {
                        notify(error.message, { type: "warning" });
                    },
                }
            );
        };

        return (
            <Toolbar>
                <CancelButton onClick={handleCancel} />
                <SaveButton label="Save & Continue" type="button" onClick={handleSaveContinue} />
                <SaveButton type="button" onClick={handleSaveClose} />
            </Toolbar>
        );
    };

    return (
        <Fragment>
            <AddButton title="Add user member" onClick={handleOpen} />
            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>Add user member</DialogTitle>
                <DialogContent>
                    <SimpleForm toolbar={<CustomToolbar />}>
                        <ReferenceInput
                            source="user"
                            reference="users"
                            label="User"
                            filter={{ exclude_product: id }}
                            sort={{ field: "full_name", order: "ASC" }}
                        >
                            <AutocompleteInputWide
                                optionText={getUserOptionText}
                                validate={validate_required}
                                onChange={(e) => setUser(e)}
                            />
                        </ReferenceInput>
                        <AutocompleteInputWide
                            source="role"
                            choices={ROLE_CHOICES}
                            validate={validate_required}
                            onChange={(e) => setRole(e)}
                        />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default ProductMemberAdd;
