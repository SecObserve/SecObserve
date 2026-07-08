import { Stack } from "@mui/material";
import { useState } from "react";
import { Edit, SaveButton, SimpleForm, Toolbar, WithRecord, useRecordContext } from "react-admin";

import { Product } from "../types";
import ProductDeleteAction from "./ProductDeleteAction";
import ProductDeleteApproval from "./ProductDeleteApproval";
import { ProductCreateEditComponent, transform } from "./functions";

const CustomToolbar = () => {
    const product = useRecordContext<Product>();

    return (
        <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
            <SaveButton alwaysEnable />
            <Stack direction="row" spacing={1}>
                <ProductDeleteApproval product={product} resource="products" isProductGroup={false} />
                <ProductDeleteAction product={product} resource="products" isProductGroup={false} />
            </Stack>
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
