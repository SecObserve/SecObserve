import { Stack, Typography } from "@mui/material";
import { Labeled, RecordContextProvider, ReferenceField, TextField } from "react-admin";

import license_components from ".";
import { EvaluationResultField } from "../../commons/custom_fields/EvaluationResultField";
import { useStyles } from "../../commons/layout/themes";

type LicenseComponentShowLicenseProps = {
    licenseComponent: any;
    direction: "row" | "column";
};

const LicenseComponentShowLicense = ({ licenseComponent, direction }: LicenseComponentShowLicenseProps) => {
    const { classes } = useStyles();

    let spacing = 8;
    if (direction == "column") {
        spacing = 2;
        classes.fontBigBold = "";
    }

    return (
        <RecordContextProvider value={licenseComponent}>
            {direction === "row" && (
                <Typography variant="h6" sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}>
                    <license_components.icon />
                    &nbsp;&nbsp;License
                </Typography>
            )}
            {direction === "column" && (
                <Typography variant="h6" sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}>
                    License
                </Typography>
            )}
            <Stack spacing={2}>
                <Stack spacing={spacing} direction={direction}>
                    {licenseComponent.imported_declared_license_name === "No license information" &&
                        licenseComponent.imported_concluded_license_name === "No license information" &&
                        licenseComponent.manual_concluded_license_name === "No license information" && (
                            <Labeled label="Effective license">
                                <TextField
                                    source="effective_license_name"
                                    sx={{ fontStyle: "italic" }}
                                    className={classes.fontBigBold}
                                />
                            </Labeled>
                        )}
                    {licenseComponent.imported_declared_spdx_license && (
                        <Labeled label="Imported declared SPDX Id">
                            <ReferenceField
                                source="imported_declared_spdx_license"
                                reference="licenses"
                                link="show"
                                sx={{ "& a": { textDecoration: "none" } }}
                            >
                                <TextField source="spdx_id_name" className={classes.fontBigBold} />
                            </ReferenceField>
                        </Labeled>
                    )}
                    {licenseComponent.imported_declared_license_expression && (
                        <Labeled label="Imported declared license expression">
                            <TextField source="imported_declared_license_expression" className={classes.fontBigBold} />
                        </Labeled>
                    )}
                    {licenseComponent.imported_declared_non_spdx_license && (
                        <Labeled label="Imported declared non-SPDX license">
                            <TextField
                                source="imported_declared_non_spdx_license"
                                sx={{ fontStyle: "italic" }}
                                className={classes.fontBigBold}
                            />
                        </Labeled>
                    )}
                    {licenseComponent.imported_declared_multiple_licenses && (
                        <Labeled label="Imported declared multiple licenses">
                            <TextField
                                source="imported_declared_multiple_licenses"
                                sx={{ fontStyle: "italic" }}
                                className={classes.fontBigBold}
                            />
                        </Labeled>
                    )}
                    {!licenseComponent.imported_declared_spdx_license &&
                        !licenseComponent.imported_declared_license_expression &&
                        !licenseComponent.imported_declared_non_spdx_license &&
                        !licenseComponent.imported_declared_multiple_licenses &&
                        licenseComponent.imported_declared_license_name !== "No license information" && (
                            <Labeled label="Imported declared license">
                                <TextField
                                    source="imported_declared_license_name"
                                    sx={{ fontStyle: "italic" }}
                                    className={classes.fontBigBold}
                                />
                            </Labeled>
                        )}
                    {licenseComponent.imported_concluded_spdx_license && (
                        <Labeled label="Imported concluded SPDX Id">
                            <ReferenceField
                                source="imported_concluded_spdx_license"
                                reference="licenses"
                                link="show"
                                sx={{ "& a": { textDecoration: "none" } }}
                            >
                                <TextField source="spdx_id_name" className={classes.fontBigBold} />
                            </ReferenceField>
                        </Labeled>
                    )}
                    {licenseComponent.imported_concluded_license_expression && (
                        <Labeled label="Imported concluded license expression">
                            <TextField source="imported_concluded_license_expression" className={classes.fontBigBold} />
                        </Labeled>
                    )}
                    {licenseComponent.imported_concluded_non_spdx_license && (
                        <Labeled label="Imported concluded non-SPDX license">
                            <TextField
                                source="imported_concluded_non_spdx_license"
                                sx={{ fontStyle: "italic" }}
                                className={classes.fontBigBold}
                            />
                        </Labeled>
                    )}
                    {licenseComponent.imported_concluded_multiple_licenses && (
                        <Labeled label="Imported concluded multiple licenses">
                            <TextField
                                source="imported_concluded_multiple_licenses"
                                sx={{ fontStyle: "italic" }}
                                className={classes.fontBigBold}
                            />
                        </Labeled>
                    )}
                    {!licenseComponent.imported_concluded_spdx_license &&
                        !licenseComponent.imported_concluded_license_expression &&
                        !licenseComponent.imported_concluded_non_spdx_license &&
                        !licenseComponent.imported_concluded_multiple_licenses &&
                        licenseComponent.imported_concluded_license_name !== "No license information" && (
                            <Labeled label="Imported concluded license">
                                <TextField
                                    source="imported_concluded_license_name"
                                    sx={{ fontStyle: "italic" }}
                                    className={classes.fontBigBold}
                                />
                            </Labeled>
                        )}
                    <Stack spacing={1}>
                        {licenseComponent.manual_concluded_spdx_license && (
                            <Labeled label="Manual concluded SPDX Id">
                                <ReferenceField
                                    source="manual_concluded_spdx_license"
                                    reference="licenses"
                                    link="show"
                                    sx={{ "& a": { textDecoration: "none" } }}
                                >
                                    <TextField source="spdx_id_name" className={classes.fontBigBold} />
                                </ReferenceField>
                            </Labeled>
                        )}
                        {licenseComponent.manual_concluded_license_expression && (
                            <Labeled label="Manual concluded license expression">
                                <TextField
                                    source="manual_concluded_license_expression"
                                    className={classes.fontBigBold}
                                />
                            </Labeled>
                        )}
                        {licenseComponent.manual_concluded_non_spdx_license && (
                            <Labeled label="Manual concluded non-SPDX license">
                                <TextField
                                    source="manual_concluded_non_spdx_license"
                                    sx={{ fontStyle: "italic" }}
                                    className={classes.fontBigBold}
                                />
                            </Labeled>
                        )}
                        {!licenseComponent.manual_concluded_spdx_license &&
                            !licenseComponent.manual_concluded_license_expression &&
                            !licenseComponent.manual_concluded_non_spdx_license &&
                            licenseComponent.manual_concluded_license_name !== "No license information" && (
                                <Labeled label="Manual concluded license">
                                    <TextField
                                        source="manual_concluded_license_name"
                                        sx={{ fontStyle: "italic" }}
                                        className={classes.fontBigBold}
                                    />
                                </Labeled>
                            )}
                        {licenseComponent.manual_concluded_comment && (
                            <Labeled label="Manual concluded comment">
                                <TextField source="manual_concluded_comment" />
                            </Labeled>
                        )}
                    </Stack>
                </Stack>
                <Labeled label="Evaluation result">
                    <EvaluationResultField source="evaluation_result" label="Evaluation result" />
                </Labeled>
            </Stack>
        </RecordContextProvider>
    );
};

export default LicenseComponentShowLicense;
