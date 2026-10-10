import { faFileCsv, faFileExcel } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import DownloadIcon from "@mui/icons-material/Download";
import PivotTableChartIcon from "@mui/icons-material/PivotTableChart";
import { Divider, ListItemIcon } from "@mui/material";
import Button from "@mui/material/Button";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import queryString from "query-string";
import { Fragment, MouseEvent, useState } from "react";
import { useListContext, useNotify } from "react-admin";
import { useNavigate } from "react-router-dom";

import { fetch_get } from "../../access_control/auth_provider/fetch_instance";
import { getIconAndFontColor } from "../../commons/functions";
import { getOrderingQuery } from "../../commons/ra-data-django-rest-framework";

type ExportMenuProps = {
    resource?: string;
    title?: string;
};

// Exports the list with its filters and sort order, used for observations and components
const ExportMenu = ({ resource = "observations", title = "Observations" }: ExportMenuProps) => {
    const notify = useNotify();
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);
    const navigate = useNavigate();
    const { filterValues, sort } = useListContext();
    const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
        setAnchorEl(event.currentTarget);
    };
    const handleClose = () => {
        setAnchorEl(null);
    };

    const exportDataCsv = async (url: string, filename: string, message: string) => {
        fetch_get(url)
            .then(async function (response) {
                const blob = new Blob([await response.text()], { type: "text/csv" });
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
        fetch_get(url)
            .then(async function (response) {
                const blob = new Blob([await response.arrayBuffer()], {
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

    const exportExcel = async () => {
        exportDataExcel(`/${resource}/export_excel/?` + queryParams(), `${resource}.xlsx`, title);
    };

    const exportCsv = async () => {
        exportDataCsv(`/${resource}/export_csv/?` + queryParams(), `${resource}.csv`, title);
    };

    const queryParams = () => {
        const query = { ...filterValues, ...getOrderingQuery({ sort }) };
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
                slotProps={{
                    list: {
                        "aria-labelledby": "basic-button",
                    },
                }}
            >
                <MenuItem onClick={exportExcel}>
                    <ListItemIcon>
                        <FontAwesomeIcon icon={faFileExcel} color={getIconAndFontColor()} />
                    </ListItemIcon>
                    {title} / Excel
                </MenuItem>
                <MenuItem onClick={exportCsv}>
                    <ListItemIcon>
                        <FontAwesomeIcon icon={faFileCsv} color={getIconAndFontColor()} />
                    </ListItemIcon>
                    {title} / CSV
                </MenuItem>
                {resource === "observations" && <Divider />}
                {resource === "observations" && (
                    <MenuItem
                        onClick={() => {
                            navigate("/pivot_table?" + queryParams());
                            handleClose();
                        }}
                    >
                        <ListItemIcon>
                            <PivotTableChartIcon sx={{ color: getIconAndFontColor() }} />
                        </ListItemIcon>
                        Observations / Pivot Table
                    </MenuItem>
                )}
            </Menu>
        </Fragment>
    );
};

export default ExportMenu;
