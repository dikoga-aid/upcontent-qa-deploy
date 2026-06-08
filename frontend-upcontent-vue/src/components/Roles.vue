<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
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

const orgLabel = computed(() => {
  const o = orgs.value.find((x) => x.id === orgId.value);
  return o ? o.display_name || o.name : "";
});
</script>

<template>
  <main class="page-main">
    <header class="page-header">
      <h1 class="page-title">
        {{ orgLabel || "Organization" }}
        <span style="color: var(--text-3); font-size: 24px"> / Roles</span>
      </h1>
      <p class="page-sub">Manage role assignments for members of this organization.</p>
    </header>

    <div v-if="msg" :class="`alert alert-${msg.kind}`">{{ msg.text }}</div>

    <div class="org-selector-wrap">
      <label class="form-label" for="rolesOrg">Organization</label>
      <select
        id="rolesOrg"
        v-model="orgId"
        class="form-input form-select"
        style="max-width: 400px"
      >
        <option v-if="orgs.length === 0" value="">No organizations yet</option>
        <option v-for="o in orgs" :key="o.id" :value="o.id">
          {{ o.display_name || o.name }}
        </option>
      </select>
    </div>

    <section class="card card-wide">
      <div class="section-header" style="margin-bottom: 20px">
        <span class="section-icon">👥</span>
        <h2 class="card-title">Members &amp; roles</h2>
        <span class="badge badge--neutral" style="margin-left: 8px">
          {{ members.length }} member{{ members.length === 1 ? "" : "s" }}
        </span>
      </div>

      <table class="data-table">
        <thead>
          <tr>
            <th>Member</th>
            <th>Current roles</th>
            <th>Assign roles</th>
            <th>User ID</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in members" :key="m.user_id">
            <td>
              <div class="member-cell">
                <img v-if="m.picture" class="member-avatar" :src="m.picture" alt="" />
                <div v-else class="member-avatar-initials">
                  {{ (m.name || m.email || "?").substring(0, 1).toUpperCase() }}
                </div>
                <div>
                  <div style="font-size: 14px; font-weight: 500">
                    {{ m.name || m.email }}
                  </div>
                  <div style="font-size: 12px; color: var(--text-3)">{{ m.email }}</div>
                </div>
              </div>
            </td>
            <td>
              <span
                v-if="m.roles.length === 0"
                style="font-size: 13px; color: var(--text-3)"
              >
                No roles assigned
              </span>
              <div v-else style="display: flex; flex-wrap: wrap; gap: 6px">
                <span v-for="role in m.roles" :key="role.id" class="role-chip">
                  <span>{{ role.name }}</span>
                  <button title="Remove role" @click="toggle(m, role)">×</button>
                </span>
              </div>
            </td>
            <td>
              <span
                v-if="tenantRoles.length === 0"
                style="font-size: 13px; color: var(--text-3)"
              >
                No roles available
              </span>
              <div v-else class="assign-checks">
                <label v-for="role in tenantRoles" :key="role.id" :title="role.description">
                  <input
                    type="checkbox"
                    :checked="hasRole(m, role)"
                    @change="toggle(m, role)"
                  />
                  <span>{{ role.name }}</span>
                </label>
              </div>
            </td>
            <td><code style="font-size: 11px">{{ m.user_id }}</code></td>
          </tr>
          <tr v-if="members.length === 0">
            <td colspan="4" style="color: var(--text-2)">
              No members to display (or you lack read access).
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </main>
</template>
