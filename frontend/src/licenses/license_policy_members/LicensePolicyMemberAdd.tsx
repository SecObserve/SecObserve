import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { BooleanInput, CreateBase, ReferenceInput, SaveButton, SimpleForm, useNotify, useRefresh } from "react-admin";
import { useFormContext } from "react-hook-form";

import AddButton from "../../commons/custom_fields/AddButton";
import CancelButton from "../../commons/custom_fields/CancelButton";
import Toolbar from "../../commons/custom_fields/Toolbar";
import { validate_required } from "../../commons/custom_validators";
import { getUserOptionText } from "../../commons/functions";
import { AutocompleteInputWide } from "../../commons/layout/themes";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

export type LicensePolicyMemberAddProps = {
    id: any;
};

const LicensePolicyMemberAdd = ({ id }: LicensePolicyMemberAddProps) => {
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
    const [isManager, setIsManager] = useState(false);
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
                is_manager: isManager,
            };
            add_user(data, false);
        };

        const handleSaveClose = (e: any) => {
            e.preventDefault(); // necessary to prevent default SaveButton submit logic
            const data = {
                user: user,
                is_manager: isManager,
            };
            add_user(data, true);
        };

        const add_user = (data: any, close_dialog: boolean) => {
            const url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/license_policy_members/";
            const body = JSON.stringify({ license_policy: id, ...data });
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
                    <CreateBase resource="license_policy_members">
                        <SimpleForm toolbar={<CustomToolbar />}>
                            <ReferenceInput
                                source="user"
                                reference="users"
                                label="User"
                                filter={{ exclude_license_policy: id }}
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
                    </CreateBase>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default LicensePolicyMemberAdd;
