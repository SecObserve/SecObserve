import { faFileCsv, faFileExcel } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import DownloadIcon from "@mui/icons-material/Download";
import { ListItemIcon } from "@mui/material";
import Button from "@mui/material/Button";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import queryString from "query-string";
import { Fragment, MouseEvent, useState } from "react";
import { useListContext, useNotify } from "react-admin";

import axios_instance from "../../access_control/auth_provider/axios_instance";
import { getIconAndFontColor } from "../../commons/functions";

const ExportMenu = () => {
    const notify = useNotify();
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);
    const { filterValues, sort } = useListContext();
    const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
        setAnchorEl(event.currentTarget);
    };
    const handleClose = () => {
        setAnchorEl(null);
    };

    const exportDataCsv = async (url: string, filename: string, message: string) => {
        axios_instance
            .get(url)
            .then(function (response) {
                const blob = new Blob([response.data], { type: "text/csv" });
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.href = url;
                link.download = filename;
                link.click();

                notify(message + " downloaded", {
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

    const exportDataExcel = async (url: string, filename: string, message: string) => {
        axios_instance
            .get(url, {
                responseType: "arraybuffer",
                headers: { Accept: "*/*" },
            })
            .then(function (response) {
                const blob = new Blob([response.data], {
                    type: "application/zip",
                });
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.href = url;
                link.download = filename;
                link.click();

                notify(message + " downloaded", {
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

    const exportObservationsExcel = async () => {
        exportDataExcel("/observations/export_excel/?" + queryParams(), "open_observations.xlsx", "Observations");
    };

    const exportObservationsCsv = async () => {
        exportDataCsv("/observations/export_csv/?" + queryParams(), "open_observations.csv", "Observations");
    };

    const queryParams = () => {
        const query = { ...filterValues, ...sort };
        return queryString.stringify(query);
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
                MenuListProps={{
                    "aria-labelledby": "basic-button",
                }}
            >
                <MenuItem onClick={exportObservationsExcel}>
                    <ListItemIcon>
                        <FontAwesomeIcon icon={faFileExcel} color={getIconAndFontColor()} />
                    </ListItemIcon>
                    Observations / Excel
                </MenuItem>
                <MenuItem onClick={exportObservationsCsv}>
                    <ListItemIcon>
                        <FontAwesomeIcon icon={faFileCsv} color={getIconAndFontColor()} />
                    </ListItemIcon>
                    Observations / CSV
                </MenuItem>
            </Menu>
        </Fragment>
    );
};

export default ExportMenu;
