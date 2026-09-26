import { Stack } from "@mui/material";
import { Fragment } from "react";
import {
    BooleanField,
    BooleanInput,
    ChipField,
    FormDataConsumer,
    Labeled,
    ReferenceArrayField,
    ReferenceArrayInput,
    SingleFieldList,
    useRecordContext,
} from "react-admin";

import { DesignatedApproversInput } from "../../../commons/custom_fields/DesignatedApproversInput";
import { AutocompleteArrayInputWide } from "../../../commons/layout/themes";

export const ReviewInputs = () => {
    const product_group = useRecordContext();
    // Limit approver choices to members with an approval-capable role on this product group.
    const approver_filter = { assessment_approver_for_product: product_group?.id ?? 0 };

    return (
        <>
            <BooleanInput source="assessments_need_approval" label="Assessments need approval" defaultValue={false} />
            <FormDataConsumer>
                {({ formData }) =>
                    formData.assessments_need_approval && (
                        <Fragment>
                            <DesignatedApproversInput
                                approver_filter={approver_filter}
                                helperText="Users allowed to approve assessments for all products in this group. Empty for default permission."
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
                                    helperText="Groups whose members may approve assessments for all products in this group."
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

export const isReviewVisible = (product_group: any) =>
    Boolean(
        product_group.assessments_need_approval ||
        product_group.product_rules_need_approval ||
        product_group.new_observations_in_review
    );

export const ReviewFields = () => {
    const product_group: any = useRecordContext();
    if (!product_group) {
        return null;
    }

    return (
        <Stack spacing={1}>
            {product_group.assessments_need_approval && (
                <Labeled label="Assessments need approval">
                    <BooleanField source="assessments_need_approval" />
                </Labeled>
            )}
            {product_group.assessment_approvers && product_group.assessment_approvers.length > 0 && (
                <Labeled label="Designated approvers">
                    <ReferenceArrayField source="assessment_approvers" reference="users">
                        <SingleFieldList linkType={false}>
                            <ChipField source="full_name" size="small" />
                        </SingleFieldList>
                    </ReferenceArrayField>
                </Labeled>
            )}
            {product_group.assessment_approver_authorization_groups &&
                product_group.assessment_approver_authorization_groups.length > 0 && (
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
            {product_group.product_rules_need_approval && (
                <Labeled label="Rules need approval">
                    <BooleanField source="product_rules_need_approval" />
                </Labeled>
            )}
            {product_group.new_observations_in_review && (
                <Labeled label='Status "In review" for new observations'>
                    <BooleanField source="new_observations_in_review" />
                </Labeled>
            )}
        </Stack>
    );
};
