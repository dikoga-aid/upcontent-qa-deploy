<script setup lang="ts">
import { ref } from "vue";
import { useAuth0 } from "@auth0/auth0-vue";
import Landing from "./components/Landing.vue";
import Portal from "./components/Portal.vue";
import Plans from "./components/Plans.vue";
import Organizations from "./components/Organizations.vue";
import Roles from "./components/Roles.vue";

const { isAuthenticated, isLoading, user, error, loginWithRedirect, logout } = useAuth0();
const tab = ref("portal");
const tabs = ["portal", "plans", "organizations", "roles"];

function doLogout() {
  logout({ logoutParams: { returnTo: window.location.origin } });
}
</script>

<template>
  <div class="demo-ribbon">DEMO</div>
  <div class="demo-banner">
    DEMO — not a production system; do not enter real credentials.
  </div>

  <div class="nav">
    <span class="brand">Sniply<span class="dot">.</span></span>
    <template v-if="isAuthenticated">
      <button
        v-for="t in tabs"
        :key="t"
        class="btn ghost"
        :style="{ textTransform: 'capitalize', opacity: tab === t ? 1 : 0.7 }"
        @click="tab = t"
      >
        {{ t }}
      </button>
    </template>
    <span class="spacer" />
    <template v-if="isAuthenticated">
      <span class="muted">{{ user?.name || user?.email }}</span>
      <button class="btn" @click="doLogout">Log out</button>
    </template>
    <button v-else class="btn" @click="loginWithRedirect()">Log in</button>
  </div>

  <div v-if="error" class="container">
    <div class="notice error">Auth error: {{ error.message }}</div>
  </div>

  <div v-if="isLoading" class="container"><p class="muted">Loading…</p></div>
  <Landing v-else-if="!isAuthenticated" />
  <Portal v-else-if="tab === 'portal'" />
  <Plans v-else-if="tab === 'plans'" />
  <Organizations v-else-if="tab === 'organizations'" />
  <Roles v-else />
</template>
