import { maxLength, maxValue, minValue, required } from "react-admin";

import { getServerDate } from "./time_zone";

export const validate_required = [required()];

export const validate_required_32 = [required(), maxLength(32)];
export const validate_required_150 = [required(), maxLength(150)];
export const validate_required_255 = [required(), maxLength(255)];
export const validate_required_2048 = [required(), maxLength(2048)];
export const validate_required_4096 = [required(), maxLength(4096)];

export const validate_150 = [maxLength(150)];
export const validate_255 = [maxLength(255)];
export const validate_513 = [maxLength(513)];
export const validate_2048 = [maxLength(2048)];

export const validate_0_10 = [minValue(0), maxValue(10)];
export const validate_0_999999 = [minValue(0), maxValue(999999)];
export const validate_1_4096 = [minValue(1), maxValue(4096)];
export const validate_1_999999 = [minValue(1), maxValue(999999)];
export const validate_2000_9999 = [minValue(2000), maxValue(9999)];

export function validate_after_today() {
    return [minValue(getServerDate(new Date(Date.now() + 24 * 60 * 60 * 1000)))];
}
