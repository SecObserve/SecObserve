import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { BooleanInput, ReferenceInput, SaveButton, SimpleForm, useNotify, useRefresh } from "react-admin";
import { useFormContext } from "react-hook-form";

import AddButton from "../../commons/custom_fields/AddButton";
import CancelButton from "../../commons/custom_fields/CancelButton";
import Toolbar from "../../commons/custom_fields/Toolbar";
import { validate_required } from "../../commons/custom_validators";
import { getUserOptionText } from "../../commons/functions";
import { AutocompleteInputWide } from "../../commons/layout/themes";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

export type AuthorizationGroupMemberAddProps = {
    id: any;
};

const AuthorizationGroupMemberAdd = ({ id }: AuthorizationGroupMemberAddProps) => {
    const [open, setOpen] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();
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
    const [is_manager, setIsManager] = useState(false);
    const resetState = () => {
        setUser(undefined);
        setIsManager(false);
    };

    const CustomToolbar = () => {
        const { reset } = useFormContext();

        const handleSaveContinue = (e: any) => {
            e.preventDefault(); // necessary to prevent default SaveButton submit logic
            const data = {
                user: user,
                is_manager: is_manager,
            };
            add_user(data, false);
        };

        const handleSaveClose = (e: any) => {
            e.preventDefault(); // necessary to prevent default SaveButton submit logic
            const data = {
                user: user,
                is_manager: is_manager,
            };
            add_user(data, true);
        };

        const add_user = (data: any, close_dialog: boolean) => {
            const url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/authorization_group_members/";
            const body = JSON.stringify({ authorization_group: id, ...data });
            httpClient(url, {
                method: "POST",
                body: body,
            })
                .then(() => {
                    refresh();
                    notify("User added", { type: "success" });
                    resetState();
                    reset();
                    if (close_dialog) {
                        setOpen(false);
                    }
                })
                .catch((error) => {
                    notify(error.message, { type: "warning" });
                });
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
            <AddButton title="Add user" onClick={handleOpen} />
            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>Add user</DialogTitle>
                <DialogContent>
                    <SimpleForm toolbar={<CustomToolbar />}>
                        <ReferenceInput
                            source="user"
                            reference="users"
                            label="User"
                            filter={{ exclude_authorization_group: id }}
                            sort={{ field: "full_name", order: "ASC" }}
                        >
                            <AutocompleteInputWide
                                optionText={getUserOptionText}
                                validate={validate_required}
                                onChange={(e) => setUser(e)}
                            />
                        </ReferenceInput>
                        <BooleanInput
                            source="dummy_is_manager"
                            label="Manager"
                            defaultValue={false}
                            onChange={(e) => setIsManager(e.target.checked)}
                        />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default AuthorizationGroupMemberAdd;
