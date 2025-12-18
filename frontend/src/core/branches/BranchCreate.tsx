import { Dialog, DialogContent, DialogTitle, Stack } from "@mui/material";
import { Fragment, useState } from "react";
import { BooleanInput, CreateBase, SimpleForm, useCreate, useNotify, useRefresh } from "react-admin";

import AddButton from "../../commons/custom_fields/AddButton";
import OSVLinuxDistributionInput from "../../commons/custom_fields/OSVLinuxDistributionInput";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { validate_255, validate_required_255 } from "../../commons/custom_validators";
import { TextInputWide } from "../../commons/layout/themes";

export type BranchCreateProps = {
    product: any;
};

const BranchCreate = ({ product }: BranchCreateProps) => {
    const [open, setOpen] = useState(false);
    const refresh = useRefresh();
    const notify = useNotify();
    const [create] = useCreate();
    const handleOpen = () => setOpen(true);
    const handleCancel = () => setOpen(false);
    const handleClose = (event: object, reason: string) => {
        if (reason && reason == "backdropClick") return;
        setOpen(false);
    };

    const create_branch = (data: any) => {
        data.product = product.id;

        if (!data.purl) {
            data.purl = "";
        }
        if (!data.cpe23) {
            data.cpe23 = "";
        }
        if (!data.osv_linux_distribution) {
            data.osv_linux_distribution = "";
        }
        if (!data.osv_linux_release) {
            data.osv_linux_release = "";
        }

        create(
            "branches",
            { data: data },
            {
                onSuccess: () => {
                    refresh();
                    notify("Branch / version added", { type: "success" });
                    setOpen(false);
                },
                onError: (error: any) => {
                    notify(error.message, { type: "warning" });
                },
            }
        );
    };

    return (
        <Fragment>
            <AddButton title="Add branch / version" onClick={handleOpen} />
            <Dialog open={open} onClose={handleClose} maxWidth={"lg"}>
                <DialogTitle>Add branch / version</DialogTitle>
                <DialogContent>
                    <CreateBase resource="branches">
                        <SimpleForm onSubmit={create_branch} toolbar={<ToolbarCancelSave onClick={handleCancel} />}>
                            <TextInputWide source="name" validate={validate_required_255} />
                            <BooleanInput source="is_default_branch" label="Default branch / version" defaultValue={product.repository_default_branch === null}/>
                            <TextInputWide source="purl" label="PURL" validate={validate_255} />
                            <TextInputWide source="cpe23" label="CPE 2.3" validate={validate_255} />
                            <BooleanInput
                                source="housekeeping_protect"
                                label="Protect from housekeeping"
                                defaultValue={false}
                            />
                            {product?.osv_enabled && (
                                <Stack direction="row" spacing={2} alignItems="center">
                                    <OSVLinuxDistributionInput />
                                </Stack>
                            )}
                        </SimpleForm>
                    </CreateBase>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default BranchCreate;
