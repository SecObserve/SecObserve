import { Box } from "@mui/material";
import { WithRecord } from "react-admin";

import ObservationShowHeader from "../observations/ObservationShowHeader";
import ObservationShowOrigins from "../observations/ObservationShowOrigins";

const ObservationLogShowAside = () => {
    return (
        <WithRecord
            render={(observation_log) => (
                <Box sx={{ width: "100%", marginLeft: 2, marginRight: 1 }}>
                    <ObservationShowHeader observation={observation_log.observation_data} />
                    <ObservationShowOrigins
                        observation={observation_log.observation_data}
                        showDependencies={false}
                        elevated={true}
                    />
                </Box>
            )}
        />
    );
};

export default ObservationLogShowAside;
