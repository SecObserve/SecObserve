import { RaRecord } from "react-admin";

// The status after the approval, an assessment that doesn't change the status leaves it empty
export const approvalStatus = (observation_log: RaRecord): string =>
    observation_log.status || observation_log.observation_data?.current_status;
