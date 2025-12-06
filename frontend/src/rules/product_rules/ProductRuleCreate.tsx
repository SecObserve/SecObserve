import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useRef, useState } from "react";
import { CreateBase, SimpleForm, useCreate, useNotify, useRefresh } from "react-admin";

import AddButton from "../../commons/custom_fields/AddButton";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { OBSERVATION_STATUS_OPEN } from "../../core/types";
import { RuleCreateEditComponent, non_duplicate_transform, validateRuleForm } from "../functions";

export type ProductRuleCreateProps = {
    product: any;
};

const ProductRuleCreate = ({ product }: ProductRuleCreateProps) => {
    const dialogRef = useRef<HTMLDivElement>(null);
    const [description, setDescription] = useState("");
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

    const create_product_rule = (data: any) => {
        data.product = product.id;
        data = non_duplicate_transform(data, description);

        create(
            "product_rules",
            { data: data },
            {
                onSuccess: () => {
                    refresh();
                    notify("Product rule added", { type: "success" });
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
            <AddButton title="Add product rule" onClick={handleOpen} />
            <Dialog ref={dialogRef} open={open} onClose={handleClose} maxWidth={"lg"}>
                <DialogTitle>Add product rule</DialogTitle>
                <DialogContent>
                    <CreateBase resource="product_rules">
                        <SimpleForm
                            onSubmit={create_product_rule}
                            toolbar={<ToolbarCancelSave onClick={handleCancel} />}
                            validate={validateRuleForm}
                        >
                            <RuleCreateEditComponent
                                product={product}
                                initialStatus={OBSERVATION_STATUS_OPEN}
                                initialDescription=""
                                setDescription={setDescription}
                                dialogRef={dialogRef}
                            />
                        </SimpleForm>
                    </CreateBase>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default ProductRuleCreate;
