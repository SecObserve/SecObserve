import DocumentScannerIcon from "@mui/icons-material/DocumentScanner";
import Button from "@mui/material/Button";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import { Fragment, MouseEvent, useState } from "react";

import CreateScanCodeIOProject from "./CreateScanCodeIOProject";

interface ScanCodeIOMenuProps {
    product: any;
}

const ScanCodeIOMenu = ({ product }: ScanCodeIOMenuProps) => {
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
                id="scancodeio-button"
                aria-controls={open ? "scancodeio-menu" : undefined}
                aria-haspopup="true"
                aria-expanded={open ? "true" : undefined}
                onClick={handleClick}
                size="small"
                sx={{ paddingTop: 0, paddingBottom: 0, paddingLeft: "5px", paddingRight: "5px" }}
                startIcon={<DocumentScannerIcon />}
            >
                ScanCode.io
            </Button>
            <Menu id="scancodeio-menu" anchorEl={anchorEl} open={open} onClose={handleClose} keepMounted>
                <MenuItem onClick={handleClose} onKeyDown={(e) => e.stopPropagation()}>
                    <CreateScanCodeIOProject product={product} />
                </MenuItem>
            </Menu>
        </Fragment>
    );
};

export default ScanCodeIOMenu;
