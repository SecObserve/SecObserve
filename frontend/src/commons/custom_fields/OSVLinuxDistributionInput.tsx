import { Fragment } from "react";
import { TextInput } from "react-admin";

import { AutocompleteInputMedium } from "../layout/themes";
import TextUrlField from "./TextUrlField";

const DISTRIBUTION_CHOICES = [
    { id: "AlmaLinux", name: "AlmaLinux" },
    { id: "Alpine", name: "Alpine" },
    { id: "Azure Linux", name: "Azure Linux" },
    { id: "Chainguard", name: "Chainguard" },
    { id: "Debian", name: "Debian" },
    { id: "Mageia", name: "Mageia" },
    { id: "openSUSE", name: "openSUSE" },
    { id: "Photon OS", name: "Photon OS" },
    { id: "Red Hat", name: "Red Hat" },
    { id: "Rocky Linux", name: "Rocky Linux" },
    { id: "SUSE", name: "SUSE" },
    { id: "TuxCare", name: "TuxCare" },
    { id: "Ubuntu", name: "Ubuntu" },
    { id: "Wolfi", name: "Wolfi" },
];

const OSVLinuxDistributionInput = () => {
    return (
        <Fragment>
            <AutocompleteInputMedium
                source="osv_linux_distribution"
                label="OSV Linux distribution"
                choices={DISTRIBUTION_CHOICES}
            />
            <TextInput source="osv_linux_release" label="OSV Linux release" />
            <TextUrlField
                url="https://ossf.github.io/osv-schema/#affectedpackage-field"
                text="OSV affected package specification"
                new_tab={true}
            />
        </Fragment>
    );
};

export default OSVLinuxDistributionInput;
