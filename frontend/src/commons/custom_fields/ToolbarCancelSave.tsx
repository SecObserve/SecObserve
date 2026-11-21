import { ReactNode } from "react";
import { SaveButton } from "react-admin";

import CancelButton from "../../commons/custom_fields/CancelButton";
import Toolbar from "../../commons/custom_fields/Toolbar";

interface ToolbarCancelSaveProps {
    onClick: () => void;
    saveButtonLabel?: string;
    saveButtonIcon?: ReactNode;
    alwaysEnable?: boolean;
    disabled?: boolean;
}

export const ToolbarCancelSave = ({
    onClick,
    saveButtonLabel,
    saveButtonIcon,
    alwaysEnable,
    disabled,
}: ToolbarCancelSaveProps) => (
    <Toolbar>
        <CancelButton onClick={onClick} />
        {/* alwaysEnable overrides disabled in the SaveButton, so it must be switched off while disabled */}
        <SaveButton
            label={saveButtonLabel || undefined}
            icon={saveButtonIcon ?? undefined}
            alwaysEnable={alwaysEnable && !disabled}
            disabled={disabled}
        />
    </Toolbar>
);
