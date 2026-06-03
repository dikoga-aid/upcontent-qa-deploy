<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
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

const currentPlan = computed(
  () => orgs.value.find((o) => o.id === orgId.value)?.selected_plan || null,
);
</script>

<template>
  <main class="page-main">
    <header class="page-header">
      <h1 class="page-title">Choose your plan</h1>
      <p class="page-sub">Select the organization and the plan that applies to it.</p>
    </header>

    <div v-if="msg" :class="`alert alert-${msg.kind}`">{{ msg.text }}</div>

    <!-- Organization selector -->
    <div class="org-selector-wrap">
      <label class="form-label" for="orgPicker">Organization</label>
      <div
        v-if="orgs.length === 0"
        class="alert alert-error"
        style="max-width: 500px"
      >
        You are not a member of any organization. Create one in the Organization
        tab first.
      </div>
      <template v-else>
        <select
          id="orgPicker"
          v-model="orgId"
          class="form-input form-select"
          style="max-width: 400px"
        >
          <option v-for="o in orgs" :key="o.id" :value="o.id">
            {{ o.display_name || o.name }}{{ o.selected_plan ? ` (${o.selected_plan})` : "" }}
          </option>
        </select>
        <p class="form-hint" style="margin-top: 6px">
          Plan will be applied to the selected organization.
        </p>
      </template>
    </div>

    <!-- Plan cards -->
    <div class="plans-grid">
      <div
        v-for="p in plans"
        :key="p.id"
        :class="`plan-card${p.display_name === 'Professional' ? ' plan-card--featured' : ''}${
          currentPlan === p.id ? ' plan-card--active' : ''
        }`"
      >
        <div v-if="p.display_name === 'Professional'" class="featured-badge">
          Most popular
        </div>

        <div class="plan-header">
          <h2 class="plan-name">{{ p.display_name }}</h2>
          <div class="plan-price">{{ p.price }}</div>
          <p class="plan-desc">{{ p.description }}</p>
        </div>

        <div v-if="currentPlan === p.id" class="plan-check">
          <span class="check-icon">✓</span> Current plan
        </div>

        <div class="plan-form">
          <button
            :class="`btn btn-full ${
              currentPlan === p.id
                ? 'btn-selected'
                : p.display_name === 'Professional'
                  ? 'btn-primary'
                  : 'btn-outline'
            }`"
            :disabled="currentPlan === p.id"
            @click="choose(p.id)"
          >
            {{ currentPlan === p.id ? "Current plan" : "Select plan" }}
          </button>
        </div>
      </div>
    </div>
  </main>
</template>
