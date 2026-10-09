import { ReactNode, createContext, useContext, useEffect, useMemo, useState } from "react";
import { SortPayload } from "react-admin";

type FilterValues = Record<string, any> | undefined;

type FilterValuesContextValue = {
    filterValues: FilterValues;
    sort: SortPayload | undefined;
    setFilterValues: (filterValues: FilterValues) => void;
    setSort: (sort: SortPayload | undefined) => void;
};

// The export menu is rendered outside of the tab that holds the list with the filters
const FilterValuesContext = createContext<FilterValuesContextValue>({
    filterValues: undefined,
    sort: undefined,
    setFilterValues: () => undefined,
    setSort: () => undefined,
});

type FilterValuesProviderProps = {
    children: ReactNode;
};

export const FilterValuesProvider = ({ children }: FilterValuesProviderProps) => {
    const [filterValues, setFilterValues] = useState<FilterValues>(undefined);
    const [sort, setSort] = useState<SortPayload | undefined>(undefined);

    const value = useMemo(() => ({ filterValues, sort, setFilterValues, setSort }), [filterValues, sort]);

    return <FilterValuesContext.Provider value={value}>{children}</FilterValuesContext.Provider>;
};

export const useFilterValues = () => {
    const { filterValues, sort } = useContext(FilterValuesContext);
    return { filterValues, sort };
};

export const usePublishFilterValues = (filterValues: FilterValues, sort: SortPayload | undefined) => {
    const { setFilterValues, setSort } = useContext(FilterValuesContext);

    useEffect(() => {
        setFilterValues(filterValues);
        setSort(sort);
        return () => {
            setFilterValues(undefined);
            setSort(undefined);
        };
    }, [filterValues, sort, setFilterValues, setSort]);
};
