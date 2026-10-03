import { ReactNode, createContext, useContext, useEffect, useMemo, useState } from "react";

type FilterValues = Record<string, any> | undefined;

type FilterValuesContextValue = {
    filterValues: FilterValues;
    setFilterValues: (filterValues: FilterValues) => void;
};

// The export menu is rendered outside of the tab that holds the list with the filters
const FilterValuesContext = createContext<FilterValuesContextValue>({
    filterValues: undefined,
    setFilterValues: () => undefined,
});

type FilterValuesProviderProps = {
    children: ReactNode;
};

export const FilterValuesProvider = ({ children }: FilterValuesProviderProps) => {
    const [filterValues, setFilterValues] = useState<FilterValues>(undefined);

    const value = useMemo(() => ({ filterValues, setFilterValues }), [filterValues]);

    return <FilterValuesContext.Provider value={value}>{children}</FilterValuesContext.Provider>;
};

export const useFilterValues = () => useContext(FilterValuesContext).filterValues;

export const usePublishFilterValues = (filterValues: FilterValues) => {
    const { setFilterValues } = useContext(FilterValuesContext);

    useEffect(() => {
        setFilterValues(filterValues);
        return () => setFilterValues(undefined);
    }, [filterValues, setFilterValues]);
};
