import { Box, Paper, Stack, Typography } from "@mui/material";
import { Identifier, Labeled, RaRecord, RecordContextProvider, TextField, useGetOne } from "react-admin";
import { useParams } from "react-router-dom";

import products from ".";
import LicensesCountField from "../../commons/custom_fields/LicensesCountField";
import ObservationsCountField from "../../commons/custom_fields/ObservationsCountField";
import { ProductGroupReferenceField } from "../../commons/custom_fields/ProductGroupReferenceField";
import { SecurityGateTextField } from "../../commons/custom_fields/SecurityGateTextField";
import ShowHeaderChip from "../../commons/custom_fields/ShowHeaderChip";
import ShowHeaderDescription from "../../commons/custom_fields/ShowHeaderDescription";
import { feature_license_management, feature_show_product_header_chips } from "../../commons/functions";
import { useStyles } from "../../commons/layout/themes";
import { Product } from "../types";
import { useBranchFilter } from "./BranchFilterContext";

// The counts of a branch have the same shape as the counts of a product, so the count fields can render either of them
const useBranchRecord = (product: Product | undefined, branch_id: Identifier | undefined) => {
    // The counts of the product are the ones of its default branch, so that branch does not have to be loaded
    const load_branch = branch_id != null && Number(branch_id) !== Number(product?.repository_default_branch);
    const { data: branch } = useGetOne("branches", { id: branch_id! }, { enabled: load_branch });

    // After navigating to another product, the branch of the previous product can still be in the context
    if (!load_branch || !branch || !product || Number(branch.product) !== Number(product.id)) {
        return undefined;
    }

    return branch;
};

function has_licenses(record: RaRecord | undefined) {
    if (!record) {
        return false;
    }

    return (
        record.forbidden_licenses_count +
            record.review_required_licenses_count +
            record.unknown_licenses_count +
            record.allowed_licenses_count +
            record.ignored_licenses_count >
        0
    );
}

const ProductHeader = () => {
    const { id: id } = useParams<any>();
    const { data: product } = useGetOne<Product>("products", { id: id });
    const { classes } = useStyles();
    const { observationsBranch, licensesBranch } = useBranchFilter();
    const observations_branch = useBranchRecord(product, observationsBranch);
    const licenses_branch = useBranchRecord(product, licensesBranch);
    // Without a branch in the filter, the counts of the product are shown, which are the ones of the default branch
    const observations_record = observations_branch ?? product;
    const licenses_record = licenses_branch ?? product;

    function get_label(label: string, branch: RaRecord | undefined, product: Product | undefined) {
        if (branch) {
            return label + " (" + branch.name + ")";
        }
        if (product?.repository_default_branch == null) {
            return label;
        }
        return label + " (" + product.repository_default_branch_name + ")";
    }

    return (
        <RecordContextProvider value={product}>
            <Paper
                sx={{
                    padding: 2,
                    marginTop: 2,
                }}
            >
                <Typography variant="h6" sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}>
                    <products.icon />
                    &nbsp;&nbsp;Product
                </Typography>
                <Box
                    sx={{
                        alignItems: "top",
                        display: "flex",
                        justifyContent: "space-between",
                    }}
                >
                    <Stack spacing={4} direction="row">
                        {product?.product_group && (
                            <Labeled label="Product group">
                                <ProductGroupReferenceField />
                            </Labeled>
                        )}
                        <Labeled label="Product name">
                            <TextField source="name" className={classes.fontBigBold} />
                        </Labeled>
                    </Stack>
                    {product?.security_gate_passed != undefined && (
                        <Labeled>
                            <SecurityGateTextField label="Security gate" />
                        </Labeled>
                    )}
                    <Stack spacing={8} direction="row">
                        <Labeled>
                            <ObservationsCountField
                                label={get_label("Active observations", observations_branch, product)}
                                withLabel={true}
                                record={observations_record}
                            />
                        </Labeled>
                        {feature_license_management() && has_licenses(licenses_record) && (
                            <Labeled>
                                <LicensesCountField
                                    label={get_label("Licenses / Components", licenses_branch, product)}
                                    withLabel={true}
                                    record={licenses_record}
                                />
                            </Labeled>
                        )}
                    </Stack>
                </Box>
                {product?.description && <ShowHeaderDescription description={product.description} />}
                {feature_show_product_header_chips() &&
                    product &&
                    (product.repository_default_branch_name || product.last_observation_change) && (
                        <Stack direction="row" spacing={1} sx={{ marginTop: 1.5, flexWrap: "wrap" }}>
                            {product.repository_default_branch_name && (
                                <ShowHeaderChip label="Default branch" value={product.repository_default_branch_name} />
                            )}
                            {product.last_observation_change && (
                                <ShowHeaderChip
                                    label="Last change"
                                    value={new Date(product.last_observation_change).toLocaleString()}
                                />
                            )}
                        </Stack>
                    )}
            </Paper>
        </RecordContextProvider>
    );
};

export default ProductHeader;
