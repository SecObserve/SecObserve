import { Stack } from "@mui/material";
import { Fragment } from "react";
import {
    BooleanField,
    FormDataConsumer,
    Labeled,
    NullableBooleanInput,
    NumberField,
    NumberInput,
    TextField,
    useRecordContext,
} from "react-admin";

import { validate_0_999999, validate_255 } from "../../../commons/custom_validators";
import { TextInputWide } from "../../../commons/layout/themes";

export const RepositoryInputs = () => (
    <>
        <TextInputWide
            source="repository_prefix"
            helperText="URL prefix to link to a file in the source code repository"
            validate={validate_255}
            sx={{ marginBottom: 3 }}
        />
        <Stack direction="row" spacing={4}>
            <NullableBooleanInput
                source="repository_branch_housekeeping_active"
                label="Housekeeping"
                defaultValue={null}
                nullLabel="Standard"
                falseLabel="Disabled"
                trueLabel="Product specific"
                helperText="Delete inactive branches / versions"
                sx={{ marginBottom: 2 }}
            />
            <FormDataConsumer>
                {({ formData }) =>
                    formData.repository_branch_housekeeping_active && (
                        <Fragment>
                            <NumberInput
                                source="repository_branch_housekeeping_keep_inactive_days"
                                label="Keep inactive"
                                helperText="Days before inactive branches / versions and their observations are deleted"
                                defaultValue={30}
                                min={1}
                                max={999999}
                                sx={{ width: "10em" }}
                                validate={validate_0_999999}
                            />
                            <TextInputWide
                                source="repository_branch_housekeeping_exempt_branches"
                                label="Exempt branches / versions"
                                helperText="Regular expression which branches / version to exempt from deletion"
                                validate={validate_255}
                            />
                        </Fragment>
                    )
                }
            </FormDataConsumer>
        </Stack>
    </>
);

export const isRepositoryVisible = (product: any) =>
    Boolean(product.repository_prefix || product.repository_branch_housekeeping_active != null);

export const RepositoryFields = () => {
    const product: any = useRecordContext();
    if (!product) {
        return null;
    }

    return (
        <>
            {product.repository_prefix && (
                <Labeled>
                    <TextField source="repository_prefix" />
                </Labeled>
            )}
            {((!product.product_group && product.repository_branch_housekeeping_active != null) ||
                (product.product_group &&
                    product.product_group_repository_branch_housekeeping_active == null &&
                    product.repository_branch_housekeeping_active != null)) && (
                <Stack direction="row" spacing={4} sx={{ marginTop: 1 }}>
                    <Labeled label="Housekeeping">
                        <BooleanField
                            source="repository_branch_housekeeping_active"
                            valueLabelFalse="Disabled"
                            valueLabelTrue="Product specific"
                        />
                    </Labeled>
                    {product.repository_branch_housekeeping_active &&
                        product.repository_branch_housekeeping_keep_inactive_days != null && (
                            <Labeled label="Keep inactive">
                                <NumberField source="repository_branch_housekeeping_keep_inactive_days" />
                            </Labeled>
                        )}
                    {product.repository_branch_housekeeping_active &&
                        product.repository_branch_housekeeping_exempt_branches != "" && (
                            <Labeled label="Exempt branches / versions">
                                <TextField source="repository_branch_housekeeping_exempt_branches" />
                            </Labeled>
                        )}
                </Stack>
            )}
            {product.product_group && product.product_group_repository_branch_housekeeping_active != null && (
                <Labeled label="Housekeeping (from product group)">
                    <BooleanField
                        source="product_group_repository_branch_housekeeping_active"
                        valueLabelFalse="Disabled"
                        valueLabelTrue="Product group specific"
                    />
                </Labeled>
            )}
        </>
    );
};
