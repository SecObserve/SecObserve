import { RaRecord } from "react-admin";

export const commentShortened = (comment: string | null) => {
    if (comment && comment.length > 255) {
        return comment.substring(0, 255) + "...";
    }
    return comment;
};

// The status after the approval, an assessment that doesn't change the status leaves it empty
export const approvalStatus = (observation_log: RaRecord): string =>
    observation_log.status || observation_log.observation_data?.current_status;
