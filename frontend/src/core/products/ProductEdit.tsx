import { useState } from "react";
import { DeleteButton, Edit, SaveButton, SimpleForm, Toolbar, WithRecord, useRecordContext } from "react-admin";

import { PERMISSION_PRODUCT_DELETE } from "../../access_control/types";
import { ProductCreateEditComponent, transform } from "./functions";

const CustomToolbar = () => {
    const product = useRecordContext();

    return (
        <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
            <SaveButton alwaysEnable />
            {product?.permissions.includes(PERMISSION_PRODUCT_DELETE) && <DeleteButton mutationMode="pessimistic" />}
        </Toolbar>
    );
};

const ProductEdit = () => {
    const [description, setDescription] = useState("");

    const edit_transform = (data: any) => {
        return transform(data, description);
    };

    return (
        <Edit redirect="show" mutationMode="pessimistic" transform={edit_transform}>
            <SimpleForm warnWhenUnsavedChanges toolbar={<CustomToolbar />}>
                <WithRecord
                    render={(product) => (
                        <ProductCreateEditComponent
                            initialDescription={product.description}
                            setDescription={setDescription}
                        />
                    )}
                />
            </SimpleForm>
        </Edit>
    );
};

export default ProductEdit;
