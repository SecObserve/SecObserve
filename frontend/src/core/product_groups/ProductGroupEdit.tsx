import { useState } from "react";
import { Edit, SaveButton, SimpleForm, Toolbar, WithRecord, useRecordContext } from "react-admin";

import { transform_product_group_and_product } from "../functions";
import ProductDeleteAction from "../products/ProductDeleteAction";
import { ProductGroup } from "../types";
import { ProductGroupCreateEditComponent } from "./functions";

const CustomToolbar = () => {
    const product = useRecordContext<ProductGroup>();

    return (
        <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
            <SaveButton alwaysEnable />
            <ProductDeleteAction product={product} isProductGroup={true} />
        </Toolbar>
    );
};

const ProductGroupEdit = () => {
    const [description, setDescription] = useState("");

    const transform = (data: any) => {
        return transform_product_group_and_product(data, description);
    };

    return (
        <Edit redirect="show" mutationMode="pessimistic" transform={transform}>
            <SimpleForm warnWhenUnsavedChanges toolbar={<CustomToolbar />}>
                <WithRecord
                    render={(product_group) => (
                        <ProductGroupCreateEditComponent
                            initialDescription={product_group.description}
                            setDescription={setDescription}
                        />
                    )}
                />
            </SimpleForm>
        </Edit>
    );
};

export default ProductGroupEdit;
