<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { api, type OrgMember, type OrgRole, type OrgSummary } from "../api";
import { useTokenGetter } from "../useToken";

const getToken = useTokenGetter();
const orgs = ref<OrgSummary[]>([]);
const orgId = ref("");
const members = ref<OrgMember[]>([]);
const tenantRoles = ref<OrgRole[]>([]);
const msg = ref<{ kind: string; text: string } | null>(null);

onMounted(async () => {
  try {
    orgs.value = await api.listOrgs(getToken);
    if (orgs.value.length) orgId.value = orgs.value[0].id;
  } catch (e: any) {
    msg.value = { kind: "error", text: e.message };
  }
});

async function load(id: string) {
  if (!id) return;
  try {
    const data = await api.listRoles(getToken, id);
    members.value = data.members;
    tenantRoles.value = data.tenant_roles;
  } catch (e: any) {
    msg.value = { kind: "error", text: e.message };
  }
}
watch(orgId, (id) => load(id));

function hasRole(m: OrgMember, role: OrgRole) {
  return m.roles.some((r) => r.id === role.id);
}

async function toggle(m: OrgMember, role: OrgRole) {
  const has = hasRole(m, role);
  try {
    if (has) await api.removeRoles(getToken, orgId.value, m.user_id, [role.id]);
    else await api.assignRoles(getToken, orgId.value, m.user_id, [role.id]);
    msg.value = { kind: "success", text: `${has ? "Removed" : "Assigned"} "${role.name}".` };
    await load(orgId.value);
  } catch (e: any) {
    msg.value = { kind: "error", text: e.message };
  }
}
</script>

<template>
  <div class="container">
    <h2 class="section-title">Organization roles</h2>
    <div v-if="msg" :class="`notice ${msg.kind}`">{{ msg.text }}</div>
    <label>Organization</label>
    <select v-model="orgId">
      <option v-if="orgs.length === 0" value="">No organizations yet</option>
      <option v-for="o in orgs" :key="o.id" :value="o.id">
        {{ o.display_name || o.name }}
      </option>
    </select>

    <table style="margin-top: 16px">
      <thead>
        <tr>
          <th>Member</th>
          <th v-for="r in tenantRoles" :key="r.id">{{ r.name }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="m in members" :key="m.user_id">
          <td>
            <div style="font-weight: 600">{{ m.name || m.user_id }}</div>
            <div class="muted" style="font-size: 12px">{{ m.email }}</div>
          </td>
          <td v-for="r in tenantRoles" :key="r.id">
            <button
              :class="`btn ${hasRole(m, r) ? '' : 'ghost'}`"
              style="padding: 4px 10px; font-size: 12px"
              @click="toggle(m, r)"
            >
              {{ hasRole(m, r) ? "Assigned" : "Assign" }}
            </button>
          </td>
        </tr>
        <tr v-if="members.length === 0">
          <td :colspan="1 + tenantRoles.length" class="muted">
            No members to display (or you lack read access).
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
