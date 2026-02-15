import { Box, Paper, Stack, Typography } from "@mui/material";
import { Labeled, RecordContextProvider, ReferenceField, TextField, useGetOne } from "react-admin";
import { useParams } from "react-router-dom";

import products from ".";
import LicensesCountField from "../../commons/custom_fields/LicensesCountField";
import ObservationsCountField from "../../commons/custom_fields/ObservationsCountField";
import { SecurityGateTextField } from "../../commons/custom_fields/SecurityGateTextField";
import { feature_license_management } from "../../commons/functions";
import { useStyles } from "../../commons/layout/themes";
import { Product } from "../types";

const ProductHeader = () => {
    const { id: id } = useParams<any>();
    const { data: product } = useGetOne<Product>("products", { id: id });
    const { classes } = useStyles();

    function get_open_observations_label(product: Product | undefined) {
        if (product?.repository_default_branch == null) {
            return "Active observations";
        }
        return "Active observations (" + product.repository_default_branch_name + ")";
    }

    function get_licenses_label(product: Product | undefined) {
        if (product?.repository_default_branch == null) {
            return "Licenses / Components";
        }
        return "Licenses / Components (" + product.repository_default_branch_name + ")";
    }

    return (
        <RecordContextProvider value={product}>
            <Paper
                sx={{
                    padding: 2,
                    marginTop: 2,
                }}
            >
                <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
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
                                <ReferenceField
                                    source="product_group"
                                    reference="product_groups"
                                    queryOptions={{ meta: { api_resource: "product_group_names" } }}
                                    link="show"
                                    sx={{ "& a": { textDecoration: "none" } }}
                                >
                                    <TextField source="name" />
                                </ReferenceField>
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
                            <ObservationsCountField label={get_open_observations_label(product)} withLabel={true} />
                        </Labeled>
                        {feature_license_management() &&
                            product &&
                            product.forbidden_licenses_count +
                                product.review_required_licenses_count +
                                product.unknown_licenses_count +
                                product.allowed_licenses_count +
                                product.ignored_licenses_count >
                                0 && (
                                <Labeled>
                                    <LicensesCountField label={get_licenses_label(product)} withLabel={true} />
                                </Labeled>
                            )}
                    </Stack>
                </Box>
            </Paper>
        </RecordContextProvider>
    );
};

export default ProductHeader;
