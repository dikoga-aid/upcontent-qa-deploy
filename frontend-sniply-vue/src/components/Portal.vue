<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useAuth0 } from "@auth0/auth0-vue";
import { api, type OrgSummary } from "../api";
import { useTokenGetter } from "../useToken";

const { user } = useAuth0();
const getToken = useTokenGetter();
const perms = ref<string[]>([]);
const orgs = ref<OrgSummary[]>([]);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    const me = await api.me(getToken);
    perms.value = me.permissions || [];
    orgs.value = await api.listOrgs(getToken);
  } catch (e: any) {
    error.value = e.message || "Failed to load portal.";
  }
});
</script>

<template>
  <div class="container">
    <h2 class="section-title">Portal</h2>
    <div v-if="error" class="notice error">{{ error }}</div>
    <div class="grid cols-2">
      <div class="card">
        <h3>Profile</h3>
        <div class="row" style="margin-top: 8px">
          <img
            v-if="user?.picture"
            :src="user.picture"
            width="48"
            height="48"
            style="border-radius: 50%"
            alt=""
          />
          <div>
            <div style="font-weight: 700">{{ user?.name }}</div>
            <div class="muted">{{ user?.email }}</div>
          </div>
        </div>
      </div>
      <div class="card">
        <h3>Token permissions</h3>
        <p v-if="perms.length === 0" class="muted">
          No permissions in token. Assign a role to your user in Auth0.
        </p>
        <div v-else class="row" style="flex-wrap: wrap; gap: 6px">
          <code v-for="p in perms" :key="p">{{ p }}</code>
        </div>
      </div>
    </div>

    <h2 class="section-title">Your organizations</h2>
    <p v-if="orgs.length === 0" class="muted">
      You are not a member of any organization yet. Create one in the
      Organizations tab.
    </p>
    <div v-else class="grid cols-3">
      <div v-for="o in orgs" :key="o.id" class="card">
        <h3 style="font-size: 16px">{{ o.display_name || o.name }}</h3>
        <div class="muted" style="font-size: 12px">{{ o.id }}</div>
        <div style="margin-top: 10px">
          <span v-if="o.selected_plan" class="plan-badge">{{ o.selected_plan }}</span>
          <span v-else class="tag">no plan</span>
        </div>
      </div>
    </div>
  </div>
</template>
