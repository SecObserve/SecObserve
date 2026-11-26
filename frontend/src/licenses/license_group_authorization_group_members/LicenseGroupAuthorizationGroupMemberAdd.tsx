import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { BooleanInput, ReferenceInput, SaveButton, SimpleForm, useNotify, useRefresh } from "react-admin";
import { useFormContext } from "react-hook-form";

import AddButton from "../../commons/custom_fields/AddButton";
import CancelButton from "../../commons/custom_fields/CancelButton";
import Toolbar from "../../commons/custom_fields/Toolbar";
import { validate_required } from "../../commons/custom_validators";
import { AutocompleteInputWide } from "../../commons/layout/themes";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

export type LicenseGroupAuthorizationGroupMemberAddProps = {
    id: any;
};

const LicenseGroupAuthorizationGroupMemberAdd = ({ id }: LicenseGroupAuthorizationGroupMemberAddProps) => {
    const [open, setOpen] = useState(false);
    const [saving, setSaving] = useState(false);
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

    const [authorization_group, setAuthorizationGroup] = useState();
    const [is_manager, setIsManager] = useState(false);
    const resetState = () => {
        setAuthorizationGroup(undefined);
        setIsManager(false);
    };

    const CustomToolbar = () => {
        const { reset } = useFormContext();

        const handleSaveContinue = (e: any) => {
            e.preventDefault(); // necessary to prevent default SaveButton submit logic
            const data = {
                authorization_group: authorization_group,
                is_manager: is_manager,
            };
            add_authorization_group(data, false);
        };

        const handleSaveClose = (e: any) => {
            e.preventDefault(); // necessary to prevent default SaveButton submit logic
            const data = {
                authorization_group: authorization_group,
                is_manager: is_manager,
            };
            add_authorization_group(data, true);
        };

        const add_authorization_group = (data: any, close_dialog: boolean) => {
            const url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/license_group_authorization_group_members/";
            const body = JSON.stringify({ license_group: id, ...data });
            setSaving(true);
            httpClient(url, {
                method: "POST",
                body: body,
            })
                .then(() => {
                    refresh();
                    notify("Authorization group added", { type: "success" });
                    resetState();
                    reset();
                    if (close_dialog) {
                        setOpen(false);
                    }
                })
                .catch((error) => {
                    notify(error.message, { type: "warning" });
                })
                .finally(() => setSaving(false));
        };

        return (
            <Toolbar>
                <CancelButton onClick={handleCancel} />
                <SaveButton disabled={saving} label="Save & Continue" type="button" onClick={handleSaveContinue} />
                <SaveButton disabled={saving} type="button" onClick={handleSaveClose} />
            </Toolbar>
        );
    };

    return (
        <Fragment>
            <AddButton title="Add authorization group" onClick={handleOpen} />
            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>Add authorization group</DialogTitle>
                <DialogContent>
                    <SimpleForm toolbar={<CustomToolbar />}>
                        <ReferenceInput
                            source="authorization_group"
                            reference="authorization_groups"
                            queryOptions={{ meta: { api_resource: "authorization_group_names" } }}
                            label="Authorization group"
                            filter={{ exclude_license_group: id }}
                            sort={{ field: "name", order: "ASC" }}
                        >
                            <AutocompleteInputWide
                                optionText="name"
                                validate={validate_required}
                                onChange={(e) => setAuthorizationGroup(e)}
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

export default LicenseGroupAuthorizationGroupMemberAdd;
