import { useState } from "react";
import { Confirm, useDelete, useNotify, useRefresh } from "react-admin";

import RemoveButton from "../../commons/custom_fields/RemoveButton";

type ProductAuthorizationGroupMemberDeleteProps = {
    product_authorization_group_member: any;
};

const ProductAuthorizationGroupMemberDelete = (props: ProductAuthorizationGroupMemberDeleteProps) => {
    const [open, setOpen] = useState(false);
    const [deleteOne, { isPending }] = useDelete();
    const refresh = useRefresh();
    const notify = useNotify();
    const handleClick = () => setOpen(true);
    const handleDialogClose = () => setOpen(false);

    const handleConfirm = async () => {
        deleteOne(
            "product_authorization_group_members",
            { id: props.product_authorization_group_member.id },
            {
                onSuccess: () => {
                    setOpen(false);
                    refresh();
                    notify("Authorization group member deleted", {
                        type: "success",
                    });
                },
                onError: (error: any) => {
                    notify("Authorization group member could not be deleted: " + error.message, {
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
                title="Remove authorization group member"
                content={
                    "Are you sure you want to remove the authorization group member " +
                    props.product_authorization_group_member.authorization_group_data.name +
                    "?"
                }
                onConfirm={handleConfirm}
                onClose={handleDialogClose}
            />
        </>
    );
};

export default ProductAuthorizationGroupMemberDelete;
