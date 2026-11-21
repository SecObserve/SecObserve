import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useState } from "react";
import { CreateBase, ReferenceInput, SaveButton, SimpleForm, useNotify, useRefresh } from "react-admin";
import { useFormContext } from "react-hook-form";

import AddButton from "../../commons/custom_fields/AddButton";
import CancelButton from "../../commons/custom_fields/CancelButton";
import Toolbar from "../../commons/custom_fields/Toolbar";
import { validate_255, validate_required } from "../../commons/custom_validators";
import { AutocompleteInputExtraWide, AutocompleteInputMedium, TextInputExtraWide } from "../../commons/layout/themes";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { EVALUATION_RESULT_CHOICES } from "../types";

export type LicensePolicyItemAddProps = {
    id: any;
};

const LicensePolicyItemAdd = ({ id }: LicensePolicyItemAddProps) => {
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

    const [licenseGroup, setLicenseGroup] = useState();
    const [license, setLicense] = useState();
    const [licenseExpression, setLicenseExpression] = useState();
    const [nonSPDXLicense, setNonSPDXLicense] = useState();
    const [evaluationResult, setEvaluationResult] = useState();
    const [comment, setComment] = useState();

    const resetState = () => {
        setLicenseGroup(undefined);
        setLicense(undefined);
        setLicenseExpression(undefined);
        setNonSPDXLicense(undefined);
        setEvaluationResult(undefined);
        setComment(undefined);
    };

    const CustomToolbar = () => {
        const { reset } = useFormContext();

        const handleSaveContinue = (e: any) => {
            e.preventDefault(); // necessary to prevent default SaveButton submit logic
            add_item(setData(), false);
        };

        const handleSaveClose = (e: any) => {
            e.preventDefault(); // necessary to prevent default SaveButton submit logic
            add_item(setData(), true);
        };

        const setData = () => {
            const data = {
                license_group: licenseGroup,
                license: license,
                license_expression: licenseExpression,
                non_spdx_license: nonSPDXLicense,
                evaluation_result: evaluationResult,
                comment: comment,
            };
            return data;
        };

        const add_item = (data: any, close_dialog: boolean) => {
            if (!data.license_expression) {
                data.license_expression = "";
            }
            if (!data.non_spdx_license) {
                data.non_spdx_license = "";
            }
            if (!data.comment) {
                data.comment = "";
            }
            const url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/license_policy_items/";
            const body = JSON.stringify({ license_policy: id, ...data });
            setSaving(true);
            httpClient(url, {
                method: "POST",
                body: body,
            })
                .then(() => {
                    refresh();
                    notify("Item added", { type: "success" });
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
            <AddButton title="Add license policy item" onClick={handleOpen} />
            <Dialog open={open} onClose={handleClose} maxWidth={"lg"}>
                <DialogTitle>Add license policy item</DialogTitle>
                <DialogContent>
                    <CreateBase resource="license_policy_items">
                        <SimpleForm toolbar={<CustomToolbar />}>
                            <ReferenceInput
                                source="license_group"
                                reference="license_groups"
                                label="License group"
                                filter={{ exclude_license_policy: id }}
                                sort={{ field: "name", order: "ASC" }}
                            >
                                <AutocompleteInputExtraWide optionText="name" onChange={(e) => setLicenseGroup(e)} />
                            </ReferenceInput>
                            <ReferenceInput
                                source="license"
                                reference="licenses"
                                filter={{ exclude_license_policy: id }}
                                sort={{ field: "spdx_id", order: "ASC" }}
                            >
                                <AutocompleteInputExtraWide
                                    label="SPDX License"
                                    optionText="spdx_id_name"
                                    onChange={(e) => setLicense(e)}
                                />
                            </ReferenceInput>
                            <TextInputExtraWide
                                source="license_expression"
                                label="License expression"
                                validate={validate_255}
                                onChange={(e) => setLicenseExpression(e.target.value)}
                            />
                            <TextInputExtraWide
                                source="non_spdx_license"
                                label="Non-SPDX license"
                                validate={validate_255}
                                onChange={(e) => setNonSPDXLicense(e.target.value)}
                            />
                            <AutocompleteInputMedium
                                source="evaluation_result"
                                label="Evaluation result"
                                choices={EVALUATION_RESULT_CHOICES}
                                validate={validate_required}
                                onChange={(e) => setEvaluationResult(e)}
                            />
                            <TextInputExtraWide
                                source="comment"
                                label="Comment"
                                validate={validate_255}
                                onChange={(e) => setComment(e.target.value)}
                            />
                        </SimpleForm>
                    </CreateBase>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default LicensePolicyItemAdd;
