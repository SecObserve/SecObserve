import DescriptionIcon from "@mui/icons-material/Description";
import DownloadIcon from "@mui/icons-material/Download";
import { ListItemIcon } from "@mui/material";
import Button from "@mui/material/Button";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import { Fragment, MouseEvent, useState } from "react";
import { useNotify } from "react-admin";

import { fetch_get } from "../../access_control/auth_provider/fetch_instance";
import { getIconAndFontColor } from "../../commons/functions";

interface ExportMenuProps {
    license_policy: any;
}

const ExportMenu = ({ license_policy }: ExportMenuProps) => {
    const notify = useNotify();
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);
    const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
        setAnchorEl(event.currentTarget);
    };
    const handleClose = () => {
        setAnchorEl(null);
    };

    const exportLicensePolicyJSON = async () => {
        exportLicensePolicy("json");
    };

    const exportLicensePolicyYAML = async () => {
        exportLicensePolicy("yaml");
    };

    const exportLicensePolicySBOMUtility = async () => {
        exportLicensePolicy("sbom_utility");
    };

    const exportLicensePolicy = async (format: string) => {
        const type = format === "yaml" ? "yaml" : "json";

        fetch_get("/license_policies/" + license_policy.id + "/export_" + format + "/")
            .then(async function (response) {
                let blob;
                if (format === "json" || format === "sbom_utility") {
                    blob = new Blob([JSON.stringify(await response.json(), null, 4)], { type: "application/json" });
                } else {
                    blob = new Blob([await response.text()], { type: "application/" + type });
                }
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.href = url;
                link.download = "license_policy_" + license_policy.id + "." + type;
                link.click();

                notify("License Policy downloaded", {
                    type: "success",
                });
            })
            .catch(function (error) {
                notify(error.message, {
                    type: "warning",
                });
            });
        handleClose();
    };

    return (
        <Fragment>
            <Button
                id="export-button"
                aria-controls={open ? "export-menu" : undefined}
                aria-haspopup="true"
                aria-expanded={open ? "true" : undefined}
                onClick={handleClick}
                size="small"
                sx={{ paddingTop: 0, paddingBottom: 0, paddingLeft: "5px", paddingRight: "5px" }}
                startIcon={<DownloadIcon />}
            >
                Export
            </Button>
            <Menu
                id="basic-menu"
                anchorEl={anchorEl}
                open={open}
                onClose={handleClose}
                slotProps={{
                    list: {
                        "aria-labelledby": "basic-button",
                    },
                }}
            >
                <MenuItem onClick={exportLicensePolicyJSON}>
                    <ListItemIcon>
                        <DescriptionIcon sx={{ color: getIconAndFontColor() }} />
                    </ListItemIcon>
                    JSON
                </MenuItem>
                <MenuItem onClick={exportLicensePolicyYAML}>
                    <ListItemIcon>
                        <DescriptionIcon sx={{ color: getIconAndFontColor() }} />
                    </ListItemIcon>
                    YAML
                </MenuItem>
                <MenuItem onClick={exportLicensePolicySBOMUtility}>
                    <ListItemIcon>
                        <DescriptionIcon sx={{ color: getIconAndFontColor() }} />
                    </ListItemIcon>
                    sbom-utility
                </MenuItem>
            </Menu>
        </Fragment>
    );
};

export default ExportMenu;
