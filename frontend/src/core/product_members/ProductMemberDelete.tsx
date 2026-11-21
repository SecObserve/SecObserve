import { useState } from "react";
import { Confirm, useDelete, useNotify, useRefresh } from "react-admin";

import RemoveButton from "../../commons/custom_fields/RemoveButton";

type ProductMemberDeleteProps = {
    product_member: any;
};

const ProductMemberDelete = (props: ProductMemberDeleteProps) => {
    const [open, setOpen] = useState(false);
    const [deleteOne, { isPending }] = useDelete();
    const refresh = useRefresh();
    const notify = useNotify();
    const handleClick = () => setOpen(true);
    const handleDialogClose = () => setOpen(false);

    const handleConfirm = async () => {
        deleteOne(
            "product_members",
            { id: props.product_member.id },
            {
                onSuccess: () => {
                    setOpen(false);
                    refresh();
                    notify("User member deleted", {
                        type: "success",
                    });
                },
                onError: (error: any) => {
                    notify("User member could not be deleted: " + error.message, {
                        type: "warning",
                    });
                },
            }
        );
    };

    return (
        <>
            <RemoveButton title="Remove" onClick={handleClick} />
            <Confirm
                loading={isPending}
                isOpen={open}
                title="Remove user member"
                content={
                    "Are you sure you want to remove the user member " + props.product_member.user_data.full_name + "?"
                }
                onConfirm={handleConfirm}
                onClose={handleDialogClose}
            />
        </>
    );
};

export default ProductMemberDelete;
