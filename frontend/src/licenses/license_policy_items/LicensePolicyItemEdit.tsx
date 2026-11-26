import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { ReferenceInput, SimpleForm, useNotify, useRefresh, useUpdate } from "react-admin";

import EditButton from "../../commons/custom_fields/EditButton";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_255, validate_required } from "../../commons/custom_validators";
import { AutocompleteInputExtraWide, AutocompleteInputMedium, TextInputExtraWide } from "../../commons/layout/themes";
import { EVALUATION_RESULT_CHOICES } from "../types";

export type LicensePolicyItemEditProps = {
    license_policy_id: any;
    license_policy_item_id: any;
};

const LicensePolicyItemEdit = ({ license_policy_id, license_policy_item_id }: LicensePolicyItemEditProps) => {
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

    const item_update = async (data: any) => {
        if (!data.license_expression) {
            data.license_expression = "";
        }
        if (!data.non_spdx_license) {
            data.non_spdx_license = "";
        }
        if (!data.comment) {
            data.comment = "";
        }

        const patch = {
            license_group: data.license_group,
            license: data.license,
            license_expression: data.license_expression,
            non_spdx_license: data.non_spdx_license,
            evaluation_result: data.evaluation_result,
            comment: data.comment,
        };

        update(
            "license_policy_items",

            {
                id: license_policy_item_id,
                data: patch,
            },
            {
                onSuccess: () => {
                    refresh();
                    notify("License policy item updated", {
                        type: "success",
                    });
                    setOpen(false);
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
            <Dialog open={open} onClose={handleClose} maxWidth={"lg"}>
                <DialogTitle>Edit license policy item</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={item_update}
                        toolbar={<ToolbarCancelSave disabled={isPending} onClick={handleCancel} />}
                    >
                        <ReferenceInput
                            source="license_group"
                            reference="license_groups"
                            label="License group"
                            filter={{ exclude_license_policy: license_policy_id }}
                            sort={{ field: "name", order: "ASC" }}
                        >
                            <AutocompleteInputExtraWide optionText="name" />
                        </ReferenceInput>
                        <ReferenceInput
                            source="license"
                            reference="licenses"
                            queryOptions={{ meta: { api_resource: "license_names" } }}
                            filter={{ exclude_license_policy: license_policy_id }}
                            sort={{ field: "spdx_id", order: "ASC" }}
                        >
                            <AutocompleteInputExtraWide label="SPDX License" optionText="spdx_id_name" />
                        </ReferenceInput>
                        <TextInputExtraWide
                            source="license_expression"
                            label="License expression"
                            validate={validate_255}
                        />
                        <TextInputExtraWide
                            source="non_spdx_license"
                            label="Non-SPDX license"
                            validate={validate_255}
                        />
                        <AutocompleteInputMedium
                            source="evaluation_result"
                            label="Evaluation result"
                            choices={EVALUATION_RESULT_CHOICES}
                            validate={validate_required}
                        />
                        <TextInputExtraWide source="comment" label="Comment" validate={validate_255} />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default LicensePolicyItemEdit;
