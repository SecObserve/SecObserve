import { UIEvent } from "react";
import { AutocompleteInput, AutocompleteInputProps, useChoicesContext } from "react-admin";

const PAGE_SIZE = 25;
// distance in pixels from the bottom of the list, when more entries are loaded
const LOAD_MORE_THRESHOLD = 50;

// Loads more entries of a ReferenceInput when the list of choices is scrolled to the bottom.
// Does nothing for static choices, there hasNextPage is always false.
// shortcut: each step refetches all loaded rows (page 1, bigger page size); switch to useInfiniteGetList if lists get huge.
export const useLoadMoreOnScroll = () => {
    const { hasNextPage, isFetching, perPage, setPerPage } = useChoicesContext();
    return (event: UIEvent<HTMLElement>) => {
        const { scrollTop, scrollHeight, clientHeight } = event.currentTarget;
        if (hasNextPage && !isFetching && scrollHeight - scrollTop - clientHeight < LOAD_MORE_THRESHOLD) {
            setPerPage(perPage + PAGE_SIZE);
        }
    };
};

export const AutocompleteInputLoadMore = (props: AutocompleteInputProps) => {
    const onScroll = useLoadMoreOnScroll();
    return <AutocompleteInput {...props} slotProps={{ ...props.slotProps, listbox: { onScroll: onScroll } }} />;
};
