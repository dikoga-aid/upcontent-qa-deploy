<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, type OrgSummary, type Plan } from "../api";
import { useTokenGetter } from "../useToken";

const getToken = useTokenGetter();
const plans = ref<Plan[]>([]);
const orgs = ref<OrgSummary[]>([]);
const orgId = ref("");
const msg = ref<{ kind: string; text: string } | null>(null);

async function reload() {
  plans.value = await api.plans(getToken);
  orgs.value = await api.listOrgs(getToken);
  if (orgs.value.length && !orgId.value) orgId.value = orgs.value[0].id;
}

onMounted(() => reload().catch((e) => (msg.value = { kind: "error", text: e.message })));

async function choose(planId: string) {
  if (!orgId.value) {
    msg.value = { kind: "error", text: "Select an organization first." };
    return;
  }
  try {
    await api.selectPlan(getToken, orgId.value, planId);
    msg.value = { kind: "success", text: `Plan ${planId} selected.` };
    await reload();
  } catch (e: any) {
    msg.value = { kind: "error", text: e.message };
  }
}
</script>

<template>
  <div class="container">
    <h2 class="section-title">Choose a plan</h2>
    <div v-if="msg" :class="`notice ${msg.kind}`">{{ msg.text }}</div>
    <label>Organization</label>
    <select v-model="orgId">
      <option v-if="orgs.length === 0" value="">No organizations yet</option>
      <option v-for="o in orgs" :key="o.id" :value="o.id">
        {{ o.display_name || o.name }} {{ o.selected_plan ? `(${o.selected_plan})` : "" }}
      </option>
    </select>
    <div class="grid cols-3" style="margin-top: 18px">
      <div v-for="p in plans" :key="p.id" class="card">
        <h3>{{ p.display_name }}</h3>
        <div style="font-size: 24px; font-weight: 800">{{ p.price }}</div>
        <p class="muted">{{ p.description }}</p>
        <button class="btn" @click="choose(p.id)">Select {{ p.display_name }}</button>
      </div>
    </div>
  </div>
</template>
