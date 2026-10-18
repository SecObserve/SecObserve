import { Identifier } from "ra-core";
import { ReferenceInput } from "ra-ui-materialui";

import { AutocompleteInputMedium, AutocompleteInputWide } from "../layout/themes";
import { AutocompleteInputAutoWidth } from "./AutocompleteInputAutoWidth";

interface BranchReferenceInputProps {
    product: Identifier;
    source: string;
    label?: string;
    alwaysOn?: boolean;
    autoWidth?: boolean;
    defaultValue?: string;
    for_license_components?: boolean;
}

export const BranchReferenceInput = ({
    product,
    source,
    label,
    alwaysOn,
    autoWidth,
    defaultValue,
    for_license_components,
}: BranchReferenceInputProps) => {
    label = label === undefined ? "Branch / Version" : label;

    return (
        <ReferenceInput
            source={source}
            reference="branches"
            queryOptions={{ meta: { api_resource: "branch_names" } }}
            sort={{ field: "name", order: "ASC" }}
            filter={{ product: product, for_license_components: for_license_components }}
            alwaysOn={alwaysOn}
        >
            {alwaysOn && autoWidth && (
                <AutocompleteInputAutoWidth optionText="name" label={label} defaultValue={defaultValue} />
            )}
            {alwaysOn && !autoWidth && (
                <AutocompleteInputMedium optionText="name" label={label} defaultValue={defaultValue} />
            )}
            {!alwaysOn && <AutocompleteInputWide optionText="name" label={label} defaultValue={defaultValue} />}
        </ReferenceInput>
    );
};
