import ViewWeekIcon from "@mui/icons-material/ViewWeek";
import { Button, Checkbox, FormControlLabel, FormGroup, Popover } from "@mui/material";
import { Fragment, useState } from "react";

import {
    ObservationOptionalColumnEntry,
    saveObservationColumnVisible,
    useObservationColumnVisibility,
} from "../../access_control/users/functions";

type ObservationColumnsButtonProps = {
    columns: readonly ObservationOptionalColumnEntry[];
};

const ObservationColumnsButton = ({ columns }: ObservationColumnsButtonProps) => {
    const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
    const isColumnVisible = useObservationColumnVisibility();

    if (columns.length === 0) {
        return null;
    }

    return (
        <Fragment>
            <Button
                size="small"
                startIcon={<ViewWeekIcon />}
                onClick={(event) => setAnchorEl(event.currentTarget)}
                sx={{ marginBottom: 1, marginLeft: 1 }}
            >
                Columns
            </Button>
            <Popover
                open={Boolean(anchorEl)}
                anchorEl={anchorEl}
                anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
                onClose={() => setAnchorEl(null)}
            >
                <FormGroup sx={{ paddingX: 2, paddingY: 1 }}>
                    {columns.map(({ name, label }) => (
                        <FormControlLabel
                            key={name}
                            control={
                                <Checkbox
                                    checked={isColumnVisible(name)}
                                    onChange={(event) => saveObservationColumnVisible(name, event.target.checked)}
                                />
                            }
                            label={label}
                        />
                    ))}
                </FormGroup>
            </Popover>
        </Fragment>
    );
};

export default ObservationColumnsButton;
