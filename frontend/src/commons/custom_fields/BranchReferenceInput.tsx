import { Identifier } from "ra-core";
import { ReferenceInput } from "ra-ui-materialui";

import { AutocompleteInputMedium, AutocompleteInputWide } from "../layout/themes";

interface BranchReferenceInputProps {
    product: Identifier;
    source: string;
    label?: string;
    alwaysOn?: boolean;
    defaultValue?: string;
    for_license_components?: boolean;
}

export const BranchReferenceInput = ({
    product,
    source,
    label,
    alwaysOn,
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
            {alwaysOn && <AutocompleteInputMedium optionText="name" label={label} defaultValue={defaultValue} />}
            {!alwaysOn && <AutocompleteInputWide optionText="name" label={label} defaultValue={defaultValue} />}
        </ReferenceInput>
    );
};
