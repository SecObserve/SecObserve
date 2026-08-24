import { Box, Paper, Stack, Typography } from "@mui/material";
import { Labeled, RecordContextProvider, TextField, useGetOne } from "react-admin";
import { useParams } from "react-router-dom";

import product_groups from ".";
import LicensesCountField from "../../commons/custom_fields/LicensesCountField";
import ObservationsCountField from "../../commons/custom_fields/ObservationsCountField";
import ShowHeaderChip from "../../commons/custom_fields/ShowHeaderChip";
import ShowHeaderDescription from "../../commons/custom_fields/ShowHeaderDescription";
import { feature_license_management } from "../../commons/functions";
import { useStyles } from "../../commons/layout/themes";
import { ProductGroup } from "../types";

const ProductGroupHeader = () => {
    const { id: id } = useParams<any>();
    const { data: product_group } = useGetOne<ProductGroup>("product_groups", { id: id });
    const { classes } = useStyles();

    return (
        <RecordContextProvider value={product_group}>
            <Paper
                sx={{
                    padding: 2,
                    marginTop: 2,
                }}
            >
                <Typography variant="h6" sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}>
                    <product_groups.icon />
                    &nbsp;&nbsp;Product Group
                </Typography>
                <Box
                    sx={{
                        alignItems: "top",
                        display: "flex",
                        justifyContent: "space-between",
                    }}
                >
                    <Labeled label="Product Group name">
                        <TextField source="name" className={classes.fontBigBold} />
                    </Labeled>
                    <Stack spacing={8} direction="row">
                        <Labeled>
                            <ObservationsCountField label="Active observations" withLabel={true} />
                        </Labeled>
                        {feature_license_management() &&
                            product_group &&
                            product_group.forbidden_licenses_count +
                                product_group.review_required_licenses_count +
                                product_group.unknown_licenses_count +
                                product_group.allowed_licenses_count +
                                product_group.ignored_licenses_count >
                                0 && (
                                <Labeled>
                                    <LicensesCountField label="Licenses / Components" withLabel={true} />
                                </Labeled>
                            )}
                    </Stack>
                </Box>
                {product_group?.description && <ShowHeaderDescription description={product_group.description} />}
                {product_group && (
                    <Stack direction="row" spacing={1} sx={{ marginTop: 1.5, flexWrap: "wrap" }}>
                        <ShowHeaderChip label="Products" value={product_group.products_count} />
                        {product_group.product_rule_approvals > 0 && (
                            <ShowHeaderChip
                                label="Review pending"
                                value={product_group.product_rule_approvals}
                                color="warning"
                                to={"/product_groups/" + id + "/show/reviews"}
                                state={{ expand: "product_rules" }}
                            />
                        )}
                        {product_group.observation_log_approvals > 0 && (
                            <ShowHeaderChip
                                label="Approval pending"
                                value={product_group.observation_log_approvals}
                                color="warning"
                                to={"/product_groups/" + id + "/show/reviews"}
                                state={{ expand: "assessments" }}
                            />
                        )}
                    </Stack>
                )}
            </Paper>
        </RecordContextProvider>
    );
};

export default ProductGroupHeader;
