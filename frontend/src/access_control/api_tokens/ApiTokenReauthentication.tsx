import { Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle } from "@mui/material";
import { useAuth } from "react-oidc-context";

import { oidc_reauthenticate } from "../auth_provider/oidc";

export const OIDC_CODE_REAUTHENTICATION_REQUIRED = "oidc_reauthentication_required";
export const OIDC_CODE_AUTH_TIME_MISSING = "oidc_auth_time_missing";

const REAUTHENTICATION_ATTEMPTED = "api_token_reauthentication_attempted";

/** Decides how an error of the API token endpoints has to be handled.
 *
 * Returns the message to show in the re-authentication dialog or null if the error is
 * not about the age of the OIDC authentication and has to be notified as usual.
 *
 * If the OIDC provider does not send an `auth_time` claim at all, authenticating again
 * will not help. Offering it once covers providers that send the claim only when it is
 * requested with `max_age`, the guard prevents an endless loop of redirects for the
 * providers that never send it.
 */
export function get_reauthentication_message(error: any): string | null {
    const code = error?.body?.code;

    if (code === OIDC_CODE_REAUTHENTICATION_REQUIRED) {
        return error.body.message;
    }

    if (code === OIDC_CODE_AUTH_TIME_MISSING) {
        if (sessionStorage.getItem(REAUTHENTICATION_ATTEMPTED)) {
            return null;
        }
        sessionStorage.setItem(REAUTHENTICATION_ATTEMPTED, "true");
        return error.body.message;
    }

    return null;
}

export function clear_reauthentication_attempt() {
    sessionStorage.removeItem(REAUTHENTICATION_ATTEMPTED);
}

type ApiTokenReauthenticationProps = {
    message: string | null;
    onCancel: () => void;
};

const ApiTokenReauthentication = ({ message, onCancel }: ApiTokenReauthenticationProps) => {
    const auth = useAuth();

    const handleReauthenticate = () => {
        oidc_reauthenticate(auth.signinRedirect);
    };

    return (
        <Dialog open={message != null} onClose={onCancel}>
            <DialogTitle>Sign in again</DialogTitle>
            <DialogContent>
                <DialogContentText>{message}</DialogContentText>
                <DialogContentText sx={{ marginTop: 2 }}>
                    After signing in you will return to this page and can enter the data of the API token again.
                </DialogContentText>
            </DialogContent>
            <DialogActions>
                <Button variant="contained" color="inherit" onClick={onCancel}>
                    Cancel
                </Button>
                <Button variant="contained" onClick={handleReauthenticate}>
                    Sign in again
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default ApiTokenReauthentication;
