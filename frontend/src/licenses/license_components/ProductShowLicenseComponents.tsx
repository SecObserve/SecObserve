import { Paper, Typography } from "@mui/material";
import { useState } from "react";
import { Labeled, RadioButtonGroupInput, ReferenceField, SimpleForm, TextField } from "react-admin";

import { PERMISSION_PRODUCT_EDIT } from "../../access_control/types";
import LicenseComponentEmbeddedList from "../../licenses/license_components/LicenseComponentEmbeddedList";
import LicenseComponentOverview from "../../licenses/license_components/LicenseComponentOverview";
import LicensePolicyApply from "../../licenses/license_policies/LicensePolicyApply";
import { getElevation } from "../../metrics/functions";

type ProductShowLicenseComponentsProps = {
    product: any;
};

const ProductShowLicenseComponents = ({ product }: ProductShowLicenseComponentsProps) => {
    const [licenseViewState, setLicenseViewState] = useState("detail");

    const licenseView = (): string => {
        let license_view_storage = localStorage.getItem("license_view");
        if (license_view_storage === null) {
            license_view_storage = "detail";
        }
        if (license_view_storage !== licenseViewState) {
            setLicenseViewState(license_view_storage);
        }
        return license_view_storage;
    };

    const setLicenseView = (value: string) => {
        localStorage.setItem("license_view", value);
        setLicenseViewState(value);
    };

    return (
        <SimpleForm toolbar={false} sx={{ padding: 0 }}>
            <Paper
                elevation={getElevation(false)}
                sx={{
                    padding: 2,
                    alignItems: "center",
                    display: "flex",
                    justifyContent: "space-between",
                    width: "100%",
                    marginBottom: 2,
                }}
            >
                <RadioButtonGroupInput
                    source="category"
                    label="List view"
                    choices={[
                        { id: "detail", name: "Detail" },
                        { id: "overview", name: "Overview" },
                    ]}
                    defaultValue={licenseView()}
                    onChange={(e) => setLicenseView(e.target.value)}
                    helperText={false}
                    sx={{ width: "fit-content", margin: 0 }}
                />
                {product?.license_policy && (
                    <Labeled label="License policy (product)">
                        <ReferenceField
                            source="license_policy"
                            reference="license_policies"
                            link="show"
                            sx={{ "& a": { textDecoration: "none" } }}
                        >
                            <TextField source="name" />
                        </ReferenceField>
                    </Labeled>
                )}
                {product &&
                    !product.license_policy &&
                    product.product_group &&
                    product.product_group_license_policy && (
                        <Labeled label="License policy (product group)">
                            <ReferenceField
                                source="product_group_license_policy"
                                reference="license_policies"
                                link="show"
                                sx={{ "& a": { textDecoration: "none" } }}
                            >
                                <TextField source="name" />
                            </ReferenceField>
                        </Labeled>
                    )}
                {product?.permissions?.includes(PERMISSION_PRODUCT_EDIT) && <LicensePolicyApply product={product} />}
                {product && !product?.permissions?.includes(PERMISSION_PRODUCT_EDIT) && (
                    <Typography variant="body1" sx={{ width: "15em" }} />
                )}
            </Paper>
            {licenseView() === "detail" && <LicenseComponentEmbeddedList product={product} />}
            {licenseView() === "overview" && <LicenseComponentOverview product={product} />}
        </SimpleForm>
    );
};

export default ProductShowLicenseComponents;
