import { createApp } from "vue";
import { createAuth0 } from "@auth0/auth0-vue";
import { auth0Options } from "./auth-config";
import App from "./App.vue";
import "./styles.css";

createApp(App)
  .use(
    createAuth0({
      domain: auth0Options.domain,
      clientId: auth0Options.clientId,
      authorizationParams: auth0Options.authorizationParams,
      cacheLocation: auth0Options.cacheLocation,
      useRefreshTokens: auth0Options.useRefreshTokens,
    }),
  )
  .mount("#app");
