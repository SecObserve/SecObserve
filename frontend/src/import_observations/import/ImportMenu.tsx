import UploadIcon from "@mui/icons-material/Upload";
import Button from "@mui/material/Button";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import { Fragment, MouseEvent, useState } from "react";

import { feature_license_management, vulnerablecode_base_url_is_set } from "../../commons/functions";
import ApiImportObservations from "./ApiImportObservations";
import FileUploadObservations from "./FileUploadObservations";
import FileUploadSBOM from "./FileUploadSBOM";
import ScanOSV from "./ScanOSV";
import ScanVulnerableCode from "./ScanVulnerableCode";

interface ImportMenuProps {
    product: any;
}

const ImportMenu = ({ product }: ImportMenuProps) => {
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);
    const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
        setAnchorEl(event.currentTarget);
    };
    const handleClose = () => {
        setAnchorEl(null);
    };

    return (
        <Fragment>
            <Button
                id="import-button"
                aria-controls={open ? "import-menu" : undefined}
                aria-haspopup="true"
                aria-expanded={open ? "true" : undefined}
                onClick={handleClick}
                size="small"
                sx={{ paddingTop: 0, paddingBottom: 0, paddingLeft: "5px", paddingRight: "5px" }}
                startIcon={<UploadIcon />}
            >
                import
            </Button>
            <Menu id="basic-menu" anchorEl={anchorEl} open={open} onClose={handleClose}>
                <MenuItem onKeyDown={(e) => e.stopPropagation()}>
                    <FileUploadObservations />
                </MenuItem>
                {feature_license_management() && (
                    <MenuItem onKeyDown={(e) => e.stopPropagation()}>
                        <FileUploadSBOM />
                    </MenuItem>
                )}
                {product.has_api_configurations && (
                    <MenuItem onKeyDown={(e) => e.stopPropagation()}>
                        <ApiImportObservations product={product} />
                    </MenuItem>
                )}
                {product.osv_enabled && product.has_licenses && (
                    <MenuItem onKeyDown={(e) => e.stopPropagation()}>
                        <ScanOSV product={product} />
                    </MenuItem>
                )}
                {vulnerablecode_base_url_is_set() && product.vulnerablecode_enabled && product.has_licenses && (
                    <MenuItem onKeyDown={(e) => e.stopPropagation()}>
                        <ScanVulnerableCode product={product} />
                    </MenuItem>
                )}
            </Menu>
        </Fragment>
    );
};

export default ImportMenu;
