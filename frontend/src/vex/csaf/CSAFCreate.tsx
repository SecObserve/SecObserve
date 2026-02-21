import AddIcon from "@mui/icons-material/Add";
import { Backdrop, CircularProgress, Dialog, DialogContent, DialogTitle, Divider, Typography } from "@mui/material";
import { Fragment, useState } from "react";
import {
    ArrayInput,
    CreateBase,
    FormDataConsumer,
    SimpleForm,
    SimpleFormIterator,
    useNotify,
    useRefresh,
} from "react-admin";

import axios_instance from "../../access_control/auth_provider/axios_instance";
import AddButton from "../../commons/custom_fields/AddButton";
import { BranchReferenceInput } from "../../commons/custom_fields/BranchReferenceInput";
import { ProductReferenceInput } from "../../commons/custom_fields/ProductReferenceInput";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_255, validate_required, validate_required_255 } from "../../commons/custom_validators";
import { AutocompleteInputMedium, TextInputWide } from "../../commons/layout/themes";
import { CSAF_PUBLISHER_CATEGORY_CHOICES, CSAF_TLP_LABEL_CHOICES, CSAF_TRACKING_STATUS_CHOICES } from "../types";

const CSAFCreate = () => {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();
    const handleOpen = () => setOpen(true);
    const handleCancel = () => {
        setOpen(false);
        setLoading(false);
    };
    const handleClose = (event: object, reason: string) => {
        if (reason && reason == "backdropClick") return;
        setOpen(false);
        setLoading(false);
    };

    const create_csaf = async (data: any) => {
        setLoading(true);

        data.vulnerability_names = data.vulnerability_names.map((v: any) => v.name);
        data.vulnerability_names = data.vulnerability_names.filter((v: any) => v != null);

        if (data.branches) {
            data.branches = data.branches.map((v: any) => v.branch);
            data.branches = data.branches.filter((v: any) => v != null);
        }

        const url = "vex/csaf_document/create/";
        axios_instance
            .post(url, data, { responseType: "blob" })
            .then(function (response) {
                if (response.status == 204) {
                    setLoading(false);
                    notify("No vulnerabilities found to create CSAF document", {
                        type: "warning",
                    });
                } else {
                    const blob = new Blob([response.data], { type: "application/json" });
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = response.headers["content-disposition"].split("filename=")[1];
                    link.click();

                    refresh();
                    setLoading(false);
                    notify("CASF document created", {
                        type: "success",
                    });
                }
                setOpen(false);
            })
            .catch(async function (error) {
                setLoading(false);
                notify(await error.response.data.text(), {
                    type: "warning",
                });
            });
    };

    return (
        <Fragment>
            <AddButton title="Create CSAF document" onClick={handleOpen} />
            <Dialog open={open && !loading} onClose={handleClose} maxWidth={"lg"}>
                <DialogTitle>Create CSAF document</DialogTitle>
                <DialogContent>
                    <CreateBase resource="csaf">
                        <SimpleForm
                            onSubmit={create_csaf}
                            toolbar={
                                <ToolbarCancelSave
                                    onClick={handleCancel}
                                    saveButtonLabel="Create"
                                    saveButtonIcon={<AddIcon />}
                                />
                            }
                        >
                            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                CSAF
                            </Typography>
                            <ProductReferenceInput />
                            <ArrayInput source="vulnerability_names" defaultValue={""} label="Vulnerabilities">
                                <SimpleFormIterator disableReordering inline>
                                    <TextInputWide source="name" validate={validate_255} />
                                </SimpleFormIterator>
                            </ArrayInput>
                            <FormDataConsumer>
                                {({ formData }) =>
                                    formData.product && (
                                        <ArrayInput source="branches" defaultValue={""} label="Branches / Versions">
                                            <SimpleFormIterator disableReordering inline>
                                                <BranchReferenceInput
                                                    source="branch"
                                                    product={formData.product}
                                                    label="Name"
                                                />
                                            </SimpleFormIterator>
                                        </ArrayInput>
                                    )
                                }
                            </FormDataConsumer>
                            <Divider flexItem sx={{ marginBottom: 2 }} />
                            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                Document
                            </Typography>
                            <TextInputWide
                                source="document_id_prefix"
                                label="ID prefix"
                                validate={validate_required_255}
                            />
                            <TextInputWide source="title" validate={validate_required_255} />
                            <AutocompleteInputMedium
                                source="tlp_label"
                                choices={CSAF_TLP_LABEL_CHOICES}
                                label="TLP label"
                                validate={validate_required}
                            />
                            <Divider flexItem sx={{ marginBottom: 2 }} />
                            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                                Tracking and Publisher
                            </Typography>
                            <AutocompleteInputMedium
                                source="tracking_status"
                                choices={CSAF_TRACKING_STATUS_CHOICES}
                                validate={validate_required}
                            />
                            <TextInputWide source="publisher_name" validate={validate_required_255} />
                            <AutocompleteInputMedium
                                source="publisher_category"
                                choices={CSAF_PUBLISHER_CATEGORY_CHOICES}
                                validate={validate_required}
                            />
                            <TextInputWide source="publisher_namespace" validate={validate_required_255} />
                        </SimpleForm>
                    </CreateBase>
                </DialogContent>
            </Dialog>
            {loading ? (
                <Backdrop sx={{ color: "#fff", zIndex: (theme) => theme.zIndex.drawer + 1 }} open={open}>
                    <CircularProgress color="primary" />
                </Backdrop>
            ) : null}
        </Fragment>
    );
};

export default CSAFCreate;
