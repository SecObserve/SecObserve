import { getResolvedSettingTheme } from "../../access_control/users/functions";

const Logo = () => {
    if (getResolvedSettingTheme() == "dark") {
        return <img src="secobserve_white.svg" alt="SecObserve logo" height={"20px"} />;
    } else {
        return <img src="secobserve.svg" alt="SecObserve logo" height={"20px"} />;
    }
};

export default Logo;
