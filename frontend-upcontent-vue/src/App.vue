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
const tabs = [
  { id: "portal", label: "Profile" },
  { id: "plans", label: "Plans" },
  { id: "organizations", label: "Organization" },
  { id: "roles", label: "Roles" },
];

function doLogout() {
  logout({ logoutParams: { returnTo: window.location.origin } });
}
</script>

<template>
  <div class="grid-bg" />
  <div class="demo-ribbon">DEMO</div>
  <div class="demo-banner">
    DEMO — not a production system; do not enter real credentials.
  </div>

  <nav class="nav">
    <div class="nav-inner">
      <span class="logo">
        <img class="logo-img" src="/logo.svg" alt="UpContent" />
      </span>
      <div v-if="isAuthenticated" class="nav-links">
        <button
          v-for="t in tabs"
          :key="t.id"
          :class="`nav-link${tab === t.id ? ' active' : ''}`"
          @click="tab = t.id"
        >
          {{ t.label }}
        </button>
      </div>
      <div class="nav-user">
        <template v-if="isAuthenticated">
          <span class="nav-username">{{ user?.name || user?.email }}</span>
          <button class="btn btn-ghost" @click="doLogout">Sign out</button>
        </template>
        <button v-else class="btn btn-primary" @click="loginWithRedirect()">
          Sign in
        </button>
      </div>
    </div>
  </nav>

  <main v-if="error" class="page-main">
    <div class="alert alert-error">Auth error: {{ error.message }}</div>
  </main>

  <main v-if="isLoading" class="page-main">
    <p class="page-sub">Loading…</p>
  </main>
  <Landing v-else-if="!isAuthenticated" />
  <Portal v-else-if="tab === 'portal'" />
  <Plans v-else-if="tab === 'plans'" />
  <Organizations v-else-if="tab === 'organizations'" />
  <Roles v-else />
</template>
