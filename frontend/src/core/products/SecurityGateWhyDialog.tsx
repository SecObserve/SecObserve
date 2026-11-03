import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { Button, Dialog, DialogContent, DialogTitle, IconButton, Stack, Tooltip } from "@mui/material";
import { Fragment, useState } from "react";
import { useNavigate } from "react-router";

import { SecurityGatePreview } from "../../commons/security_gate/SecurityGatePreview";
import observations from "../observations";
import { OBSERVATION_STATUS_ACTIVE, Product } from "../types";

/** The observations tab with the observations the gate counts on the default branch. */
const countedObservationsUrl = (product: Product) => {
    const filter = {
        current_status: OBSERVATION_STATUS_ACTIVE,
        counted_by_security_gate: true,
        ...(product.repository_default_branch ? { branch: product.repository_default_branch } : {}),
    };
    return `/products/${product.id}/show?displayedFilters=%7B%7D&filter=${encodeURIComponent(JSON.stringify(filter))}&order=ASC&sort=current_severity`;
};

/** Explains the gate in the product header: counted and active observations per severity, whatever the gate's source. */
const SecurityGateWhyDialog = ({ product }: { product: Product }) => {
    const [open, setOpen] = useState(false);
    const navigate = useNavigate();

    return (
        <Fragment>
            <Tooltip title="Why?">
                <IconButton size="small" aria-label="Why" onClick={() => setOpen(true)}>
                    <InfoOutlinedIcon fontSize="small" />
                </IconButton>
            </Tooltip>
            <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Security gate</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ alignItems: "flex-start" }}>
                        <SecurityGatePreview />
                        <Button
                            variant="outlined"
                            size="small"
                            startIcon={<observations.icon />}
                            onClick={() => {
                                setOpen(false);
                                navigate(countedObservationsUrl(product));
                            }}
                            sx={{ textTransform: "none" }}
                        >
                            Show counted observations
                        </Button>
                    </Stack>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default SecurityGateWhyDialog;
