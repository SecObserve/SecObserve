import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { Fragment, useRef, useState } from "react";
import { CreateBase, SimpleForm, useCreate, useNotify, useRefresh } from "react-admin";

import AddButton from "../../commons/custom_fields/AddButton";
import { ToolbarCancelSave } from "../../commons/custom_fields/ToolbarCancelSave";
import { ProductCreateEditComponent } from "../products/functions";

export type ProductCreateDialogProps = {
    productGroupId: any;
};

const ProductCreateDialog = ({ productGroupId }: ProductCreateDialogProps) => {
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

    const createProduct = (data: any) => {
        data.product_group = productGroupId;
        data.description = description;

        create(
            "products",
            { data: data },
            {
                onSuccess: () => {
                    refresh();
                    notify("Product added", { type: "success" });
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
            <AddButton title="Add product" onClick={handleOpen} />
            <Dialog ref={dialogRef} open={open} onClose={handleClose} maxWidth={"lg"}>
                <DialogTitle>Add product</DialogTitle>
                <DialogContent>
                    <CreateBase resource="product">
                        <SimpleForm onSubmit={createProduct} toolbar={<ToolbarCancelSave onClick={handleCancel} />}>
                            <ProductCreateEditComponent
                                initialDescription=""
                                setDescription={setDescription}
                                productGroupId={productGroupId}
                            />
                        </SimpleForm>
                    </CreateBase>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default ProductCreateDialog;
