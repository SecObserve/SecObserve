import { Stack } from "@mui/material";
import { Fragment } from "react";
import {
    BooleanField,
    BooleanInput,
    ChipField,
    FormDataConsumer,
    Identifier,
    Labeled,
    ReferenceArrayField,
    ReferenceArrayInput,
    SingleFieldList,
    useRecordContext,
} from "react-admin";

import { DesignatedApproversInput } from "../../../commons/custom_fields/DesignatedApproversInput";
import { AutocompleteArrayInputWide } from "../../../commons/layout/themes";

export const ReviewInputs = ({ productGroupId }: { productGroupId?: Identifier }) => {
    const product = useRecordContext();
    // Limit approver choices to members with an approval-capable role on this product or its product group.
    const approver_filter = { assessment_approver_for_product: product?.id ?? productGroupId ?? 0 };

    return (
        <>
            <BooleanInput source="assessments_need_approval" label="Assessments need approval" defaultValue={false} />
            <FormDataConsumer>
                {({ formData }) =>
                    formData.assessments_need_approval && (
                        <Fragment>
                            <DesignatedApproversInput
                                approver_filter={approver_filter}
                                helperText="Users allowed to approve assessments. Empty for default permission."
                            />
                            <ReferenceArrayInput
                                source="assessment_approver_authorization_groups"
                                reference="authorization_groups"
                                filter={approver_filter}
                                sort={{ field: "name", order: "ASC" }}
                            >
                                <AutocompleteArrayInputWide
                                    label="Designated approver groups"
                                    optionText="name"
                                    helperText="Groups whose members may approve assessments."
                                />
                            </ReferenceArrayInput>
                        </Fragment>
                    )
                }
            </FormDataConsumer>
            <BooleanInput source="product_rules_need_approval" label="Rules need approval" defaultValue={false} />
            <BooleanInput
                source="new_observations_in_review"
                label='Status "In review" for new observations'
                defaultValue={false}
            />
        </>
    );
};

export const isReviewVisible = (product: any) =>
    Boolean(
        product.assessments_need_approval ||
        product.product_group_assessments_need_approval ||
        product.product_rules_need_approval ||
        product.product_group_product_rules_need_approval ||
        product.new_observations_in_review ||
        product.product_group_new_observations_in_review
    );

export const ReviewFields = () => {
    const product: any = useRecordContext();
    if (!product) {
        return null;
    }

    return (
        <Stack spacing={1}>
            <Labeled label="Assessments need approval">
                <BooleanField source="assessments_need_approval" />
            </Labeled>
            {product.product_group_assessments_need_approval && (
                <Labeled label="Assessments need approval (from product group)">
                    <BooleanField source="product_group_assessments_need_approval" />
                </Labeled>
            )}
            {product.assessment_approvers && product.assessment_approvers.length > 0 && (
                <Labeled label="Designated approvers">
                    <ReferenceArrayField source="assessment_approvers" reference="users">
                        <SingleFieldList linkType={false}>
                            <ChipField source="full_name" size="small" />
                        </SingleFieldList>
                    </ReferenceArrayField>
                </Labeled>
            )}
            {product.assessment_approver_authorization_groups &&
                product.assessment_approver_authorization_groups.length > 0 && (
                    <Labeled label="Designated approver groups">
                        <ReferenceArrayField
                            source="assessment_approver_authorization_groups"
                            reference="authorization_groups"
                        >
                            <SingleFieldList linkType={false}>
                                <ChipField source="name" size="small" />
                            </SingleFieldList>
                        </ReferenceArrayField>
                    </Labeled>
                )}
            {product.product_group_assessment_approvers && product.product_group_assessment_approvers.length > 0 && (
                <Labeled label="Designated approvers (from product group)">
                    <ReferenceArrayField source="product_group_assessment_approvers" reference="users">
                        <SingleFieldList linkType={false}>
                            <ChipField source="full_name" size="small" />
                        </SingleFieldList>
                    </ReferenceArrayField>
                </Labeled>
            )}
            {product.product_group_assessment_approver_authorization_groups &&
                product.product_group_assessment_approver_authorization_groups.length > 0 && (
                    <Labeled label="Designated approver groups (from product group)">
                        <ReferenceArrayField
                            source="product_group_assessment_approver_authorization_groups"
                            reference="authorization_groups"
                        >
                            <SingleFieldList linkType={false}>
                                <ChipField source="name" size="small" />
                            </SingleFieldList>
                        </ReferenceArrayField>
                    </Labeled>
                )}
            <Labeled label="Rules need approval">
                <BooleanField source="product_rules_need_approval" />
            </Labeled>
            {product.product_group_product_rules_need_approval && (
                <Labeled label="Rules need approval (from product group)">
                    <BooleanField source="product_group_product_rules_need_approval" />
                </Labeled>
            )}
            <Labeled label='Status "In review" for new observations'>
                <BooleanField source="new_observations_in_review" />
            </Labeled>
            {product.product_group_new_observations_in_review && (
                <Labeled label='Status "In review" for new observations (from product group)'>
                    <BooleanField source="product_group_new_observations_in_review" />
                </Labeled>
            )}
        </Stack>
    );
};
