import { Stack, Typography } from "@mui/material";
import { Labeled, TextField, useRecordContext } from "react-admin";

import product_groups from "..";
import MarkdownEdit from "../../../commons/custom_fields/MarkdownEdit";
import MarkdownField from "../../../commons/custom_fields/MarkdownField";
import { validate_required_255 } from "../../../commons/custom_validators";
import { TextInputWide } from "../../../commons/layout/themes";

type ProductGroupBasicsInputsProps = {
    initialDescription: string;
    setDescription: (value: string) => void;
};

/**
 * The first block of a product group, which is always shown and is not one of the accordion
 * sections, because it identifies the product group.
 */
export const ProductGroupBasicsInputs = ({ initialDescription, setDescription }: ProductGroupBasicsInputsProps) => (
    <>
        <Typography variant="h6" sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}>
            <product_groups.icon />
            &nbsp;&nbsp;Product Group
        </Typography>
        <TextInputWide autoFocus source="name" validate={validate_required_255} />
        <MarkdownEdit
            initialValue={initialDescription}
            setValue={setDescription}
            label="Description"
            maxLength={2048}
        />
    </>
);

export const ProductGroupBasicsFields = () => {
    const product_group: any = useRecordContext();
    if (!product_group) {
        return null;
    }

    return (
        <>
            <Typography variant="h6">Settings</Typography>
            <Stack spacing={1}>
                <Labeled>
                    <TextField source="name" />
                </Labeled>
                {product_group.description && (
                    <Labeled>
                        <MarkdownField content={product_group.description} label="Description" />
                    </Labeled>
                )}
            </Stack>
        </>
    );
};
