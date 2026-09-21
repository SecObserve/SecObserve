import { Stack, Typography } from "@mui/material";
import { Identifier, Labeled, TextField, useRecordContext } from "react-admin";

import products from "..";
import MarkdownEdit from "../../../commons/custom_fields/MarkdownEdit";
import MarkdownField from "../../../commons/custom_fields/MarkdownField";
import { ProductGroupReferenceField } from "../../../commons/custom_fields/ProductGroupReferenceField";
import { ProductGroupReferenceInput } from "../../../commons/custom_fields/ProductGroupReferenceInput";
import { validate_255, validate_required_255 } from "../../../commons/custom_validators";
import { TextInputWide } from "../../../commons/layout/themes";

type ProductBasicsInputsProps = {
    initialDescription: string;
    setDescription: (value: string) => void;
    productGroupId?: Identifier;
};

/**
 * The first block of a product, which is always shown and is not one of the accordion sections,
 * because it identifies the product.
 */
export const ProductBasicsInputs = ({
    initialDescription,
    setDescription,
    productGroupId,
}: ProductBasicsInputsProps) => (
    <>
        <Typography variant="h6" sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}>
            <products.icon />
            &nbsp;&nbsp;Product
        </Typography>
        <TextInputWide autoFocus source="name" validate={validate_required_255} />
        <MarkdownEdit
            initialValue={initialDescription}
            setValue={setDescription}
            label="Description"
            maxLength={2048}
        />
        <ProductGroupReferenceInput defaultValue={productGroupId} />
        <Stack direction="row" spacing={4}>
            <TextInputWide source="purl" validate={validate_255} label="PURL" />
            <TextInputWide source="cpe23" validate={validate_255} label="CPE 2.3" />
        </Stack>
    </>
);

export const ProductBasicsFields = () => {
    const product: any = useRecordContext();
    if (!product) {
        return null;
    }

    return (
        <>
            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                Product
            </Typography>
            <Stack spacing={1}>
                <Labeled>
                    <TextField source="name" />
                </Labeled>
                {product.description && (
                    <Labeled>
                        <MarkdownField content={product.description} label="Description" />
                    </Labeled>
                )}
                {product.product_group && (
                    <Labeled label="Product group">
                        <ProductGroupReferenceField />
                    </Labeled>
                )}
                {product.purl && (
                    <Labeled label="PURL">
                        <TextField source="purl" />
                    </Labeled>
                )}
                {product.cpe23 && (
                    <Labeled label="CPE 2.3">
                        <TextField source="cpe23" />
                    </Labeled>
                )}
            </Stack>
        </>
    );
};
