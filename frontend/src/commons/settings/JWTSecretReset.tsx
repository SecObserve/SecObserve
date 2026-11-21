import { Typography } from "@mui/material";
import { useState } from "react";
import { Confirm, useNotify } from "react-admin";

import { httpClient } from "../../commons/ra-data-django-rest-framework";
import RemoveButton from "../custom_fields/RemoveButton";

const JWTSecretReset = () => {
    const notify = useNotify();

    const [open, setOpen] = useState(false);
    const handleOpen = () => setOpen(true);
    const handleClose = () => setOpen(false);

    const handleJWTSecretReset = async () => {
        const url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/jwt_secret/reset/";
        httpClient(url, {
            method: "POST",
        })
            .then(() => {
                setOpen(false);
                notify("JWT secret reset", {
                    type: "success",
                });
            })
            .catch((error) => {
                notify(error.message, {
                    type: "warning",
                });
            });
    };

    const body = `Are you sure you want to reset the JWT secret?
    This will invalidate all existing JWT tokens.`;

    return (
        <>
            <RemoveButton title="Reset JWT secret" onClick={handleOpen} />
            <Confirm
                isOpen={open}
                title="Reset JWT secret"
                content={<Typography sx={{ whiteSpace: "pre-line" }}>{body}</Typography>}
                onConfirm={handleJWTSecretReset}
                onClose={handleClose}
            />
        </>
    );
};

export default JWTSecretReset;
