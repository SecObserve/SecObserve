import { Identifier } from "ra-core";
import { ReferenceInput } from "ra-ui-materialui";

import { AutocompleteInputMedium, AutocompleteInputWide } from "../layout/themes";
import { AutocompleteInputAutoWidth } from "./AutocompleteInputAutoWidth";

interface ProductReferenceInputProps {
    alwaysOn?: boolean;
    autoWidth?: boolean;
    defaultValue?: string;
    disabled?: boolean;
    // offers only the products of this product group
    product_group?: Identifier;
}

export const ProductReferenceInput = ({
    alwaysOn,
    autoWidth,
    defaultValue,
    disabled,
    product_group,
}: ProductReferenceInputProps) => {
    return (
        <ReferenceInput
            source="product"
            reference="products"
            queryOptions={{ meta: { api_resource: "product_names" } }}
            sort={{ field: "name", order: "ASC" }}
            filter={product_group ? { product_group: product_group } : undefined}
            alwaysOn={alwaysOn}
        >
            {alwaysOn && autoWidth && (
                <AutocompleteInputAutoWidth optionText="name" defaultValue={defaultValue} disabled={disabled} />
            )}
            {alwaysOn && !autoWidth && (
                <AutocompleteInputMedium optionText="name" defaultValue={defaultValue} disabled={disabled} />
            )}
            {!alwaysOn && <AutocompleteInputWide optionText="name" defaultValue={defaultValue} disabled={disabled} />}
        </ReferenceInput>
    );
};
