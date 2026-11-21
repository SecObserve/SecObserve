import { Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle } from "@mui/material";

import CopyToClipboardButton from "../../commons/custom_fields/CopyToClipboardButton";

type WebhookSecretDialogProps = {
    secret: string | null;
    onClose: () => void;
};

// The parent clears the secret in onClose, so it lives no longer than this dialog
const WebhookSecretDialog = ({ secret, onClose }: WebhookSecretDialogProps) => (
    <Dialog open={secret !== null} onClose={(_event, reason) => reason !== "backdropClick" && onClose()}>
        <DialogTitle>Webhook secret</DialogTitle>
        <DialogContent>
            <DialogContentText sx={{ marginBottom: 2 }}>
                Copy the secret now, it is shown only once. Use it to verify the signature of the deliveries.
            </DialogContentText>
            <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-all" }}>{secret}</pre>
        </DialogContent>
        <DialogActions>
            {secret && <CopyToClipboardButton text={secret} message="Webhook secret copied to clipboard" />}
            <Button onClick={onClose}>Close</Button>
        </DialogActions>
    </Dialog>
);

export default WebhookSecretDialog;
