import { useAuth0 } from "@auth0/auth0-react";
import { useCallback } from "react";
import type { TokenGetter } from "./api";

// Wraps getAccessTokenSilently into the TokenGetter the api helper expects.
export function useTokenGetter(): TokenGetter {
  const { getAccessTokenSilently } = useAuth0();
  return useCallback(
    () => getAccessTokenSilently(),
    [getAccessTokenSilently],
  );
}
