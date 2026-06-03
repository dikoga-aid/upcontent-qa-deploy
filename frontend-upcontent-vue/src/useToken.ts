import { useAuth0 } from "@auth0/auth0-vue";
import type { TokenGetter } from "./api";

// Provides a TokenGetter backed by getAccessTokenSilently.
export function useTokenGetter(): TokenGetter {
  const { getAccessTokenSilently } = useAuth0();
  return () => getAccessTokenSilently();
}
