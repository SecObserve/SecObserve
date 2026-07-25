import { useState } from "react";
import { Edit, SaveButton, SimpleForm, Toolbar, WithRecord, useRecordContext } from "react-admin";

import { Product } from "../types";
import ProductDeleteAction from "./ProductDeleteAction";
import { ProductCreateEditComponent, transform } from "./functions";

const CustomToolbar = () => {
    const product = useRecordContext<Product>();

    return (
        <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
            <SaveButton alwaysEnable />
            <ProductDeleteAction product={product} isProductGroup={false} />
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
