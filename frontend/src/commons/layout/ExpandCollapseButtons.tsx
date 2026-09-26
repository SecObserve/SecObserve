import UnfoldLessIcon from "@mui/icons-material/UnfoldLess";
import UnfoldMoreIcon from "@mui/icons-material/UnfoldMore";
import { Stack } from "@mui/material";

import SmallButton from "../custom_fields/SmallButton";
import { ALL_SECTIONS_CLOSED } from "./SectionAccordion";

type ExpandCollapseButtonsProps = {
    /** The labels of the sections the screen renders. */
    labels: string[];
    expandedSections: string[];
    setExpandedSections: (labels: string[]) => void;
};

/**
 * Opens or closes all sections of a screen at once, to be placed above its accordions.
 *
 * The width is needed because react-admin's SimpleForm aligns its children to the start, so that
 * the buttons would stick to the left of an edit form otherwise.
 */
const ExpandCollapseButtons = ({ labels, expandedSections, setExpandedSections }: ExpandCollapseButtonsProps) => {
    return (
        <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", width: "100%", marginBottom: 2 }}>
            <SmallButton
                title="Expand all"
                icon={<UnfoldMoreIcon />}
                disabled={expandedSections.length === labels.length}
                onClick={() => setExpandedSections(labels)}
            />
            <SmallButton
                title="Collapse all"
                icon={<UnfoldLessIcon />}
                disabled={expandedSections.length === 0}
                onClick={() => setExpandedSections(ALL_SECTIONS_CLOSED)}
            />
        </Stack>
    );
};

export default ExpandCollapseButtons;
