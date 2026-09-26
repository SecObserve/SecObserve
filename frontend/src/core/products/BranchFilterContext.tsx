import { ReactNode, createContext, useContext, useEffect, useMemo, useState } from "react";
import { Identifier } from "react-admin";

type BranchFilterTarget = "observations" | "licenses";

type BranchFilterContextValue = {
    observationsBranch: Identifier | undefined;
    licensesBranch: Identifier | undefined;
    setObservationsBranch: (branch: Identifier | undefined) => void;
    setLicensesBranch: (branch: Identifier | undefined) => void;
};

// The header with the counts is rendered outside of the tabs that hold the lists with the branch filters
const BranchFilterContext = createContext<BranchFilterContextValue>({
    observationsBranch: undefined,
    licensesBranch: undefined,
    setObservationsBranch: () => undefined,
    setLicensesBranch: () => undefined,
});

type BranchFilterProviderProps = {
    children: ReactNode;
};

export const BranchFilterProvider = ({ children }: BranchFilterProviderProps) => {
    const [observationsBranch, setObservationsBranch] = useState<Identifier | undefined>(undefined);
    const [licensesBranch, setLicensesBranch] = useState<Identifier | undefined>(undefined);

    const value = useMemo(
        () => ({
            observationsBranch,
            licensesBranch,
            setObservationsBranch,
            setLicensesBranch,
        }),
        [observationsBranch, licensesBranch]
    );

    return <BranchFilterContext.Provider value={value}>{children}</BranchFilterContext.Provider>;
};

export const useBranchFilter = () => useContext(BranchFilterContext);

export const usePublishBranchFilter = (target: BranchFilterTarget, branch: Identifier | undefined, enabled = true) => {
    const { setObservationsBranch, setLicensesBranch } = useBranchFilter();

    useEffect(() => {
        if (!enabled) {
            return;
        }
        if (target === "observations") {
            setObservationsBranch(branch);
        } else {
            setLicensesBranch(branch);
        }
    }, [target, branch, enabled, setObservationsBranch, setLicensesBranch]);
};
